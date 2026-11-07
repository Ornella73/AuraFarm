"""Builder for 4-block traceable dashboard fiches (Step E4)."""
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Optional
from src.core.models import (
    Village,
    PrecalculatedSheet,
    SoilProfile,
    Variety,
    CropType,
    AlertStatus,
    ConfidenceLevel,
    RegimePluvio,
    Language
)
from src.core.database import (
    get_village_zone_mapping,
    get_phrase_recording_status_map,
    get_recent_field_observations
)
from src.data_ingestion.repositories import SpatialRepository
from src.agro_climate.water_balance import (
    calculate_hargreaves_samani_et0,
    SoilWaterReservoir,
    calculate_sowing_window
)

import jinja2
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True
)

def render_fiche_card_html(f: Dict[str, Any]) -> str:
    """Render a single 4-block fiche card into HTML using Jinja2."""
    template = jinja_env.get_template("fiche_card.html")
    return template.render(f=f)

VILLAGE_PCODES: Dict[str, str] = {
    "TG_MAR_ZIO_01": "TG01",
    "TG_MAR_LAC_02": "TG02",
    "TG_MAR_YOT_03": "TG03",
    "TG_PLA_HAH_01": "TG04",
    "TG_SAV_TON_01": "TG05",
    "TG_PLA_OGO_02": "TG06",
    "TG_PLA_KLO_03": "TG07",
    "TG_CEN_TCH_01": "TG08",
    "TG_CEN_SOT_02": "TG09",
    "TG_KAR_KOZ_01": "TG10",
    "TG_KAR_BAS_02": "TG11",
    "TG_SAV_OTI_02": "TG12",
}

LANGUAGE_NAMES: Dict[Language, str] = {
    Language.EWE: "Eʋegbe (Éwé)",
    Language.KABIYE: "Kabɩyɛ (Kabiyè)",
    Language.MINA: "Mina (Gẽ)",
    Language.FRANCAIS: "Français",
}

def build_enriched_fiche_data(
    sheet: PrecalculatedSheet,
    repo: SpatialRepository,
    force_stale_hours: Optional[int] = None,
    force_soil_fallback: bool = False,
    force_contradiction: bool = False,
    force_rupture: bool = False,
    is_simulated: bool = False,
    sim_seed: int = 42
) -> Dict[str, Any]:
    """Assemble all fields for the 4 traceable blocks of each village x crop sheet."""
    v = repo.get_village(sheet.village_id)
    if not v:
        raise ValueError(f"Village {sheet.village_id} introuvable")

    soil = repo.get_soil_for_village(sheet.village_id)
    varieties = repo.list_varieties_for_crop(sheet.crop_type)
    var = next((var for var in varieties if var.variety_id == sheet.recommended_variety_id), varieties[0] if varieties else None)

    # 1. Evaluate Freshness & Time delta
    calc_dt = datetime.fromisoformat(sheet.calculation_date) if "T" in sheet.calculation_date else datetime.combine(date.fromisoformat(sheet.calculation_date), datetime.min.time(), tzinfo=timezone.utc)
    weather_dt = datetime.fromisoformat(sheet.last_weather_update) if "T" in sheet.last_weather_update else datetime.combine(date.fromisoformat(sheet.last_weather_update), datetime.min.time(), tzinfo=timezone.utc)

    hours_old = force_stale_hours if force_stale_hours is not None else max(0, int((datetime.now(timezone.utc) - weather_dt).total_seconds() / 3600.0))
    is_stale_effective = sheet.is_data_stale or (hours_old > 48)

    # 2. Relevés pluviomètres villageois récentes 24h
    obs = get_recent_field_observations(v.village_id, limit=10)
    obs_count = len(obs)
    if obs_count > 0:
        obs_vals = [o.rainfall_mm for o in obs]
        obs_vals.sort()
        median_obs = obs_vals[len(obs_vals) // 2]
        # Check variance for contradiction
        mean_obs = sum(obs_vals) / obs_count
        variance = sum((x - mean_obs) ** 2 for x in obs_vals) / obs_count
        std_obs = variance ** 0.5
        readings_summary = f"{obs_count} relevé(s), médiane {median_obs:.0f} mm"
        is_contradictory = force_contradiction or (obs_count >= 2 and std_obs > 20.0)
    else:
        readings_summary = "Aucun relevé récent (satellite CHIRPS seul)"
        is_contradictory = force_contradiction

    # 3. BLOC D: Evaluation des Alertes de Contrôle (Ordre de priorité stricte)
    if is_stale_effective:
        control_banner = {
            "type": "stale",
            "css_class": "banner-stale",
            "icon": "fa-triangle-exclamation",
            "label": f"DONNÉE PÉRIMÉE ({hours_old}h > 48h) — RÈGLE DE SÉCURITÉ ACTIVE : ATTENDRE",
            "priority_tag": "Priorité 1 - Sécurité Légale"
        }
        effective_alert = AlertStatus.ATTENDRE_CONSULTER_AGENT
        effective_conf = ConfidenceLevel.INCERTAIN
        triggered_rule = f"RÈGLE DE SÉCURITÉ N°1 : Donnée météo obsolète ({hours_old}h). Semis verrouillé."
    elif force_soil_fallback or (soil is None):
        control_banner = {
            "type": "fallback",
            "css_class": "banner-fallback",
            "icon": "fa-database",
            "label": "SOL : Profil régional par défaut (SoilGrids en repli)",
            "priority_tag": "Priorité 2 - Fallback"
        }
        effective_alert = sheet.alert_status
        effective_conf = sheet.confidence
        triggered_rule = "Avis calculé sur profil pédologique régional de repli."
    elif is_contradictory:
        control_banner = {
            "type": "contradiction",
            "css_class": "banner-contradiction",
            "icon": "fa-scale-unbalanced",
            "label": "RELEVÉS CONTRADICTOIRES : Écart pluviomètres > 20 mm — Confiance réduite",
            "priority_tag": "Priorité 3 - Cohérence"
        }
        effective_alert = sheet.alert_status
        effective_conf = ConfidenceLevel.INCERTAIN
        triggered_rule = "Relevés villageois hétérogènes. Indice de confiance dégradé à INCERTAIN."
    elif force_rupture:
        control_banner = {
            "type": "rupture",
            "css_class": "banner-rupture",
            "icon": "fa-seedling",
            "label": f"RUPTURE ITRA : {var.variety_name if var else 'Variété'} épuisée — Alternative activée",
            "priority_tag": "Priorité 4 - Intrants"
        }
        effective_alert = sheet.alert_status
        effective_conf = sheet.confidence
        triggered_rule = "Variété recommandée en rupture : proposition de semence équivalente."
    elif is_simulated:
        control_banner = {
            "type": "simulation",
            "css_class": "banner-simulation",
            "icon": "fa-flask",
            "label": f"MODE SIMULATION STOCHASTIQUE (Graine reproductible: {sim_seed})",
            "priority_tag": "Priorité 5 - Simulation"
        }
        effective_alert = sheet.alert_status
        effective_conf = sheet.confidence
        triggered_rule = f"Scénario simulé (graine {sim_seed}) : chaîne causale pluie/Tmax/sol active."
    else:
        control_banner = {
            "type": "ok",
            "css_class": "banner-ok",
            "icon": "fa-circle-check",
            "label": "Données fraîches et cohérentes (< 48 h)",
            "priority_tag": "Supervision OK"
        }
        effective_alert = sheet.alert_status
        effective_conf = sheet.confidence
        if effective_alert == AlertStatus.SEMER:
            triggered_rule = f"SEMER : Pluie 3j ({sheet.rain_last_3days_mm} mm ≥ 20 mm), séquence sèche ({sheet.dry_spell_risk_days}j ≤ 7j) et relais assuré."
        elif effective_alert == AlertStatus.RISQUE:
            triggered_rule = f"RISQUE : 20 mm atteints mais séquence sèche de {sheet.dry_spell_risk_days} jours consécutifs prévue."
        elif effective_alert == AlertStatus.ATTENDRE_CONSULTER_AGENT:
            triggered_rule = "ATTENDRE : Conditions incertaines, sollicitez votre agent d'encadrement ICAT."
        else:
            triggered_rule = f"ATTENDRE : Pluie 3j ({sheet.rain_last_3days_mm} mm < 20 mm) insuffisante pour humecter le sol."

    # 4. BLOC B: Métriques agro-climatiques
    taw_m = soil.taw_mm_m if soil else 100.0
    depth_cm = soil.depth_cm if soil else 100.0
    res = SoilWaterReservoir(taw_m, depth_cm, initial_fill_fraction=min(1.0, max(0.3, sheet.rain_last_3days_mm / max(10.0, taw_m * (depth_cm / 100.0)))))
    
    # Soil retention tier
    if taw_m >= 125.0:
        retention_label = "Forte"
    elif taw_m >= 90.0:
        retention_label = "Moyenne"
    else:
        retention_label = "Faible"

    dry_spell_threshold = 5 if taw_m < 80.0 else 7

    # Floor date label
    if v.regime_pluviometrique == RegimePluvio.UNIMODAL:
        floor_label = "10 mai (Nord)" if "SAV" in v.village_id else "01 mai (Nord/Kara)"
    elif v.regime_pluviometrique == RegimePluvio.TRANSITION_UNIMODAL:
        floor_label = "20 avril (Centre)"
    else:
        floor_label = "10 mars (Sud)"

    # Village-specific temperature & ET0 calculation
    v_seed = sum(ord(c) for c in v.village_id)
    tmax_c = round(30.2 + (v.latitude - 6.2) * 1.15 - (getattr(v, 'altitude_m', 150) / 100.0) * 0.5 + ((v_seed % 5) - 2) * 0.3, 1)
    tmin_c = round(21.4 + (v.latitude - 6.2) * 0.35 - (getattr(v, 'altitude_m', 150) / 100.0) * 0.4 + ((v_seed % 3) - 1) * 0.2, 1)
    et0_val = calculate_hargreaves_samani_et0(tmin_c=tmin_c, tmax_c=tmax_c, latitude_deg=v.latitude, day_of_year=calc_dt.timetuple().tm_yday)

    # 5. Calculate Sowing Window ("Le Bon Moment")
    window_res = calculate_sowing_window(village=v, variety=var, current_soil=soil, reference_date=calc_dt.date())
    try:
        w_start_d = date.fromisoformat(window_res.window_start)
        w_end_d = date.fromisoformat(window_res.window_end)
        w_start_str = w_start_d.strftime("%d %b")
        w_end_str = w_end_d.strftime("%d %b")
        sowing_window_label = f"{w_start_str} — {w_end_str}"
    except Exception:
        w_start_str = window_res.window_start
        w_end_str = window_res.window_end
        sowing_window_label = f"{window_res.window_start} au {window_res.window_end}"

    if effective_alert == AlertStatus.SEMER:
        sowing_box_css = "bg-emerald-50 border-emerald-300"
        sowing_pill_css = "bg-emerald-600 text-white"
        sowing_advice_text_css = "text-emerald-900"
        sowing_window_advice = f"🌱 FENÊTRE OPTIMALE EN COURS : Conditions favorables jusqu'au {w_end_str}. Période idéale pour semer."
        timeline_active_css = "bg-emerald-500 animate-pulse"
    elif effective_alert == AlertStatus.RISQUE:
        sowing_box_css = "bg-red-50 border-red-300"
        sowing_pill_css = "bg-red-600 text-white"
        sowing_advice_text_css = "text-red-900"
        sowing_window_advice = f"⚠️ PAS LE BON MOMENT : Faux départ détecté ({sheet.dry_spell_risk_days}j secs prévus). Ne pas semer."
        timeline_active_css = "bg-red-500"
    elif effective_alert == AlertStatus.ATTENDRE_CONSULTER_AGENT:
        sowing_box_css = "bg-orange-50 border-orange-300"
        sowing_pill_css = "bg-orange-600 text-white"
        sowing_advice_text_css = "text-orange-900"
        sowing_window_advice = "⛔ SÉCURITÉ ACTIVE : Données météo > 48h. Consultez votre conseiller ICAT avant de semer."
        timeline_active_css = "bg-orange-400"
    else: # ATTENDRE
        sowing_box_css = "bg-amber-50 border-amber-300"
        sowing_pill_css = "bg-amber-500 text-slate-900"
        sowing_advice_text_css = "text-amber-900"
        sowing_window_advice = f"⏳ EN ATTENTE : Réserve en eau insuffisante. Période recommandée estimée à partir du {w_start_str}."
        timeline_active_css = "bg-amber-400"

    # Soil moisture gauge & color coding
    soil_fill_pct = min(100, max(5, int(res.soil_moisture_pct)))
    if soil_fill_pct >= 50:
        soil_fill_color = "#16a34a"  # Green
    elif soil_fill_pct >= 30:
        soil_fill_color = "#d97706"  # Amber
    else:
        soil_fill_color = "#dc2626"  # Red

    # 7-day sparkline forecast distribution
    base_fc = max(2.0, sheet.rain_forecast_7days_mm)
    rain_sparkline = [
        round(sheet.rain_last_3days_mm * 0.4, 1),
        round(sheet.rain_last_3days_mm * 0.6, 1),
        round(base_fc * 0.25, 1),
        round(base_fc * 0.35, 1) if sheet.dry_spell_risk_days < 7 else 0.0,
        round(base_fc * 0.15, 1) if sheet.dry_spell_risk_days < 5 else 0.0,
        round(base_fc * 0.20, 1),
        round(base_fc * 0.05, 1)
    ]

    # 6. BLOC C: Statut et UI
    status_configs = {
        AlertStatus.SEMER: {
            "label": "SEMER DÈS MAINTENANT",
            "css": "status-semer",
            "icon": "fa-circle-check"
        },
        AlertStatus.ATTENDRE: {
            "label": "ATTENDRE",
            "css": "status-attendre",
            "icon": "fa-hourglass-half"
        },
        AlertStatus.RISQUE: {
            "label": "RISQUE FAUX DÉPART",
            "css": "status-risque",
            "icon": "fa-triangle-exclamation"
        },
        AlertStatus.ATTENDRE_CONSULTER_AGENT: {
            "label": "ATTENDRE (CONSULTER AGENT)",
            "css": "status-consulter",
            "icon": "fa-shield-halved"
        }
    }
    cfg = status_configs.get(effective_alert, status_configs[AlertStatus.ATTENDRE])

    # Audio status check
    rec_map = get_phrase_recording_status_map(v.langue_majoritaire.value)
    key_phrase = f"status_{effective_alert.value.lower()}"
    stat_audio = rec_map.get(key_phrase, "manquant")
    if stat_audio == "valide":
        audio_badge = "✅ Enregistré (locutrice)"
    elif stat_audio == "enregistre":
        audio_badge = "🟡 Enregistré (à valider)"
    else:
        audio_badge = "🟡 Voix de synthèse (fallback)"

    return {
        "village_id": v.village_id,
        "village_name": v.village_name,
        "pcode": VILLAGE_PCODES.get(v.village_id, "TG99"),
        "crop_type": sheet.crop_type.value,
        "calculation_date": calc_dt.strftime("%Y-%m-%d"),
        "calculation_time": calc_dt.strftime("%H:%M UTC") if hasattr(calc_dt, "strftime") else "06:00 UTC",
        "control_banner": control_banner,
        "rain_source": "CHIRPS v3 / ECMWF",
        "rain_source_date": weather_dt.strftime("%Y-%m-%d"),
        "is_stale": is_stale_effective,
        "soil_source": "Profil régional (fallback)" if (force_soil_fallback or soil is None) else "SoilGrids (Togo)",
        "soil_source_class": "text-amber-700" if (force_soil_fallback or soil is None) else "text-emerald-700",
        "coordinates": f"{v.latitude:.4f}°N, {v.longitude:.4f}°E",
        "village_readings_summary": readings_summary,
        "is_simulated": is_simulated,
        "sim_seed_label": f"Graine {sim_seed}",
        "rain_last_3days_mm": sheet.rain_last_3days_mm,
        "rain_decade_10days_mm": round(sheet.rain_last_3days_mm * 1.8 + 12.0, 1),
        "rain_forecast_7days_mm": sheet.rain_forecast_7days_mm,
        "dry_spell_risk_days": sheet.dry_spell_risk_days,
        "dry_spell_threshold": dry_spell_threshold,
        "tmax_forecast_3days_c": tmax_c,
        "soil_retention": retention_label,
        "soil_taw_mm_m": taw_m,
        "floor_date": floor_label,
        "soil_moisture_pct": res.soil_moisture_pct,
        "soil_fill_pct": soil_fill_pct,
        "soil_fill_color": soil_fill_color,
        "rain_sparkline": rain_sparkline,
        "sowing_window_label": sowing_window_label,
        "sowing_window_advice": sowing_window_advice,
        "sowing_box_css": sowing_box_css,
        "sowing_pill_css": sowing_pill_css,
        "sowing_advice_text_css": sowing_advice_text_css,
        "timeline_active_css": timeline_active_css,
        "region": v.region,
        "prefecture": v.prefecture,
        "daily_et0_mm": et0_val,
        "regime": v.regime_pluviometrique.value,
        "current_season": "Saison unique" if "unimodal" in v.regime_pluviometrique.value else "Grande saison (S1)",
        "triggered_rule": triggered_rule,
        "alert_status": effective_alert.value,
        "status_label": cfg["label"],
        "status_css": cfg["css"],
        "status_icon": cfg["icon"],
        "confidence": effective_conf.value,
        "recommended_variety_name": sheet.recommended_variety_name,
        "cycle_days": var.cycle_days_nominal if var else 90,
        "drought_tolerance": var.drought_tolerance if var else "Bonne",
        "advice_fr": sheet.advice_fr,
        "advice_local": sheet.advice_local,
        "langue_locale_name": LANGUAGE_NAMES.get(v.langue_majoritaire, v.langue_majoritaire.value),
        "is_translation_missing": len(sheet.advice_local.strip()) == 0,
        "audio_badge": audio_badge,
        "last_consultation": f"{calc_dt.strftime('%Y-%m-%d %H:%M')} — USSD",
        "channels": ["USSD *384*228#", "Voix IVR", "SMS"]
    }
