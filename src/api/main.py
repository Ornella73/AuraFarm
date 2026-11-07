"""FastAPI Application for AuraFarm: Telecom Webhooks, PWA Dashboard, and 2G Phone Simulator."""
import os
from datetime import datetime, date, timezone
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Form, Response, Query, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

from src.core.config import settings
from src.core.models import (
    Language,
    CropType,
    AlertStatus,
    PrecalculatedSheet,
    FieldRainObservation
)
from src.core.database import (
    init_db,
    get_precalculated_sheet,
    get_all_precalculated_sheets,
    save_field_observation,
    get_recent_field_observations,
    get_freshness_status,
    save_audio_recording,
    get_audio_recordings,
    update_audio_recording_status,
    get_phrase_recording_status_map,
    get_zone_profile,
    list_zone_profiles,
    get_village_zone_mapping,
    record_event,
    get_live_events,
    record_planting_report,
    get_planting_reports,
    save_audio_evaluation,
    list_audio_evaluations,
    get_audio_evaluations_summary
)
from src.data_ingestion.stochastic_weather import StochasticWeatherGenerator
from src.agro_climate.water_balance import (
    calculate_hargreaves_samani_et0,
    SoilWaterReservoir,
    simulate_post_sowing_21days,
    calculate_sowing_window
)
from src.agro_climate.sensitivity import (
    run_perturbation_simulation,
    compute_sensitivity_tornado,
    get_dashboard_charts_data
)
from src.data_ingestion.repositories import SpatialRepository
from src.data_ingestion.precompute_engine import PrecomputeEngine
from src.alerts.backtest import BacktestEngine
from src.channels.ussd_engine import UssdSessionEngine
from src.channels.voice_ivr import VoiceIvrEngine
from src.channels.missed_call import MissedCallHandler
from src.channels.sms_handler import SmsHandler
from src.channels.audio_registry import AudioRegistry
from src.dashboard.bulletin_generator import CommunityRadioBulletinGenerator

# Singletons
repo = SpatialRepository()
ussd_engine = UssdSessionEngine(repo=repo)
ivr_engine = VoiceIvrEngine()
missed_call_handler = MissedCallHandler(ivr_engine=ivr_engine)
sms_handler = SmsHandler()
bulletin_gen = CommunityRadioBulletinGenerator(repo=repo)
precompute_engine = PrecomputeEngine(repo=repo)
backtest_engine = BacktestEngine(repo=repo)
audio_registry = AudioRegistry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Check if precalculated sheets exist; if not, run baseline pre-calculation
    sheets = get_all_precalculated_sheets()
    if not sheets:
        precompute_engine.run_daily_pipeline()
    yield

app = FastAPI(
    title="AuraFarm API",
    description="Agro-climatic decision support for smallholder farmers in Togo (2G Feature Phones & PWA)",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# --- Telecom Webhook Endpoints ---

@app.post("/api/ussd")
def ussd_webhook(
    sessionId: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(default=""),
    serviceCode: Optional[str] = Form(default=None)
):
    """Universal USSD Webhook compatible with Africa's Talking / Yas / Moov gateways."""
    resp = ussd_engine.process_request(sessionId, phoneNumber, text)
    prefix = "END " if resp.is_terminal else "CON "
    return Response(content=f"{prefix}{resp.text}", media_type="text/plain; charset=utf-8")

@app.post("/api/ivr/webhook")
def ivr_incoming_call(
    From: str = Form(default="+22890123456"),
    To: str = Form(default="+22890000000"),
    village: Optional[str] = Query(default="TG_MAR_ZIO_01"),
    crop: Optional[str] = Query(default="mais"),
    lang: Optional[str] = Query(default="francais")
):
    """Twilio / SIP Voice IVR webhook generating TwiML response with DTMF gather."""
    c_type = CropType(crop)
    l_type = Language(lang)
    sheet = get_precalculated_sheet(village, c_type)
    
    if not sheet:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Mathieu" language="fr-FR">Bienvenue sur AuraFarm Togo. Veuillez consulter votre conseiller agricole ICAT.</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    twiml = ivr_engine.generate_twiml(sheet, l_type)
    return Response(content=twiml, media_type="application/xml")

@app.post("/api/ivr/dtmf")
def ivr_dtmf_input(
    Digits: str = Form(default="1"),
    village: str = Query(default="TG_MAR_ZIO_01"),
    crop: str = Query(default="mais"),
    lang: str = Query(default="francais")
):
    """Handles farmer keypad press during phone call (1 = replay, 2 = speak to agent)."""
    c_type = CropType(crop)
    l_type = Language(lang)
    xml_resp = ivr_engine.handle_dtmf_input(Digits, village, c_type, l_type)
    return Response(content=xml_resp, media_type="application/xml")

@app.post("/api/channels/missed-call")
def handle_missed_call(phoneNumber: str = Form(...)):
    """Receives 'bip' event from carrier and queues immediate free outbound call back."""
    result = missed_call_handler.process_incoming_bip(phoneNumber)
    return JSONResponse(content=result)

# --- Data & Agronomic Endpoints for PWA Dashboard ---

@app.get("/api/villages")
def list_villages():
    """List all registered pilot villages with coordinates, soils and dominant crops."""
    return [v.model_dump() for v in repo.list_villages()]

@app.get("/api/sheets")
def list_precalculated_sheets():
    """Fetch daily decision sheets for all villages and crops."""
    sheets = get_all_precalculated_sheets()
    return [s.model_dump() for s in sheets]

@app.get("/api/dashboard/fiches")
def get_dashboard_fiches(
    village_id: Optional[str] = None,
    crop: Optional[str] = None,
    force_stale_hours: Optional[int] = None,
    force_soil_fallback: bool = False,
    force_contradiction: bool = False,
    force_rupture: bool = False,
    is_simulated: bool = False
):
    """Retrieve all 4-block enriched traceable decision fiches for the dashboard."""
    from src.dashboard.fiche_builder import build_enriched_fiche_data, render_fiche_card_html

    sheets = get_all_precalculated_sheets()
    enriched_fiches = []
    for s in sheets:
        if village_id and s.village_id != village_id:
            continue
        if crop and s.crop_type.value != crop.lower():
            continue

        f_data = build_enriched_fiche_data(
            sheet=s,
            repo=repo,
            force_stale_hours=force_stale_hours,
            force_soil_fallback=force_soil_fallback,
            force_contradiction=force_contradiction,
            force_rupture=force_rupture,
            is_simulated=is_simulated
        )
        f_data["html"] = render_fiche_card_html(f_data)
        enriched_fiches.append(f_data)

    return enriched_fiches

@app.get("/api/dashboard/live")
def get_dashboard_live(since: Optional[str] = None, limit: int = 20):
    """Retrieve real-time event stream for dashboard polling (every 3s)."""
    events = get_live_events(since_iso=since, limit=limit)
    return {
        "events": events,
        "count": len(events),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

class EventCreatePayload(BaseModel):
    event_type: str
    village_id: str
    channel: str = "PWA"
    payload: Dict[str, Any] = {}
    phone_hash: str = "ANONYMOUS"

@app.post("/api/events")
def post_event(evt: EventCreatePayload):
    """Publish an event to the real-time stream."""
    event_id = record_event(
        event_type=evt.event_type,
        village_id=evt.village_id,
        channel=evt.channel,
        payload=evt.payload,
        phone_hash=evt.phone_hash
    )
    return {"status": "ok", "event_id": event_id}

@app.get("/api/planting-reports")
def list_planting_reports(village_id: Optional[str] = None):
    """Retrieve farmer planting declarations."""
    return get_planting_reports(village_id=village_id)

class SimulationPayload(BaseModel):
    village_id: str = "TG_MAR_ZIO_01"
    crop_type: str = "mais"
    rain_factor: float = 1.0
    temp_delta_c: float = 0.0
    taw_factor: float = 1.0
    delay_days: int = 0
    dry_spell_injection: Optional[int] = None
    dry_spell_start_day: int = 7
    seed: int = 42

@app.post("/api/simulate")
def post_simulate(payload: SimulationPayload):
    """Execute what-if perturbation simulation with < 500ms latency."""
    res = run_perturbation_simulation(
        village_id=payload.village_id,
        crop_type=payload.crop_type,
        rain_factor=payload.rain_factor,
        temp_delta_c=payload.temp_delta_c,
        taw_factor=payload.taw_factor,
        delay_days=payload.delay_days,
        dry_spell_injection=payload.dry_spell_injection,
        dry_spell_start_day=payload.dry_spell_start_day,
        seed=payload.seed
    )
    return res

@app.get("/api/sensitivity")
def get_sensitivity(village_id: str = "TG_MAR_ZIO_01", crop_type: str = "mais", seed: int = 42):
    """Get sensitivity tornado diagram data."""
    return compute_sensitivity_tornado(village_id=village_id, crop_type=crop_type, seed=seed)

@app.get("/api/dashboard/charts")
def get_dashboard_charts(village_id: str = "TG_MAR_ZIO_01", crop_type: str = "mais"):
    """Get time-series and comparison charts data for the dashboard."""
    return get_dashboard_charts_data(village_id=village_id, crop_type=crop_type)

@app.get("/api/sheet/{village_id}/{crop}")
def get_village_sheet(village_id: str, crop: str):
    """Fetch decision sheet for a specific village and crop."""
    try:
        c_type = CropType(crop.lower())
    except ValueError:
        return JSONResponse(status_code=400, content={"error": f"Invalid crop: {crop}"})
    
    sheet = get_precalculated_sheet(village_id, c_type)
    if not sheet:
        return JSONResponse(status_code=404, content={"error": "Sheet not found"})
    return sheet.model_dump()

class RainObservationPayload(BaseModel):
    village_id: str
    rainfall_mm: float
    reporter_type: str = "farmer"

@app.post("/api/observations")
def record_rain_observation(payload: RainObservationPayload):
    """Record rainfall from farmer rain gauge."""
    obs = FieldRainObservation(
        village_id=payload.village_id,
        observation_date=date.today().isoformat(),
        rainfall_mm=payload.rainfall_mm,
        reporter_type=payload.reporter_type,
        reported_at=datetime.now(timezone.utc).isoformat()
    )
    save_field_observation(obs)
    return {"status": "SUCCESS", "message": f"Pluie de {payload.rainfall_mm}mm enregistrée"}

@app.get("/api/observations/recent")
def get_all_recent_observations(limit: int = 20):
    """Get recent rain gauge submissions across all sentinel villages."""
    obs_list = get_recent_field_observations(village_id="", limit=limit)
    return [o.model_dump() for o in obs_list]

@app.get("/api/observations/{village_id}")
def get_village_observations(village_id: str):
    """Get recent rain gauge submissions for a village."""
    obs_list = get_recent_field_observations(village_id, limit=10)
    return [o.model_dump() for o in obs_list]

@app.get("/api/bulletin/{region}")
def get_radio_bulletin(region: str):
    """Generate weekly community radio broadcast script."""
    return bulletin_gen.generate_regional_bulletin(region)

@app.post("/api/pipeline/run")
def trigger_daily_pipeline(scenario: Optional[str] = Query(default=None)):
    """Manually run daily precomputation (for demo testing and scenario simulation)."""
    sheets = precompute_engine.run_daily_pipeline(simulated_weather_scenario=scenario)
    return {
        "status": "COMPLETED",
        "sheets_generated": len(sheets),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/backtest")
def run_backtest():
    """Run historical backtest validation across Togolese benchmarks."""
    return backtest_engine.run_benchmark()

@app.get("/api/health")
def healthcheck():
    """System health check & data freshness status."""
    return {
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "freshness_max_hours": settings.DATA_FRESHNESS_MAX_HOURS,
        "default_telecom_operator": settings.DEFAULT_TELECOM_OPERATOR
    }

# --- Audio Recording Kit Endpoints (Step E1) ---

@app.get("/api/audio/phrases")
def get_audio_phrases(lang: str = Query(default="ewe")):
    """List all modular phrases with current recording status for a specific language."""
    try:
        language = Language(lang.lower())
    except ValueError:
        language = Language.FRANCAIS

    status_map = get_phrase_recording_status_map(language.value)
    phrases = audio_registry.list_phrases()
    result = []
    for p in phrases:
        result.append({
            "phrase_id": p.phrase_id,
            "category": p.category,
            "text_to_read": p.get_text_for_language(language),
            "french_text": p.french_text,
            "word_count_fr": p.word_count_fr,
            "notes": p.notes,
            "status": status_map.get(p.phrase_id, "manquant")
        })
    return {"language": language.value, "count": len(result), "phrases": result}

@app.get("/api/audio/export-csv")
def export_audio_csv():
    """Download the complete phrase bank CSV for native speaker translation and validation."""
    csv_file = audio_registry.csv_path
    if not csv_file.exists():
        return JSONResponse(status_code=404, content={"error": "Phrase bank CSV not found"})
    return FileResponse(
        path=str(csv_file),
        media_type="text/csv",
        filename="aurafarm_audio_phrase_bank.csv"
    )

@app.post("/api/audio/upload")
def upload_audio_clip(
    phrase_id: str = Form(...),
    language: str = Form(...),
    speaker_id: str = Form(...),
    consent_given: int = Form(default=0),
    audio_file: UploadFile = File(...)
):
    """Upload recorded audio clip with mandatory speaker consent verification."""
    if not consent_given:
        return JSONResponse(
            status_code=400,
            content={"status": "ERROR", "error": "Le consentement explicite de la locutrice est obligatoire (Loi 2019-014)."}
        )

    try:
        lang_enum = Language(language.lower())
    except ValueError:
        return JSONResponse(status_code=400, content={"status": "ERROR", "error": f"Langue non reconnue: {language}"})

    phrase = audio_registry.get_phrase(phrase_id)
    if not phrase:
        return JSONResponse(status_code=404, content={"status": "ERROR", "error": f"Phrase ID non trouvée: {phrase_id}"})

    # Save to disk
    save_path = audio_registry.get_storage_path(lang_enum, phrase_id, speaker_id)
    content = audio_file.file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    file_size = len(content)
    # Estimate rough duration (approximate)
    duration_sec = round(file_size / (16000 * 2), 2) if file_size > 0 else 0.0

    # Save to SQLite database
    rec_id = save_audio_recording(
        phrase_id=phrase_id,
        language=lang_enum.value,
        speaker_id=speaker_id,
        consent_given=True,
        file_path=str(save_path),
        file_size_bytes=file_size,
        duration_sec=duration_sec,
        status="recorded"
    )

    return {
        "status": "SUCCESS",
        "recording_id": rec_id,
        "phrase_id": phrase_id,
        "language": lang_enum.value,
        "file_size": file_size,
        "message": "Enregistrement vocal sauvegardé avec succès."
    }

class ClipStatusUpdatePayload(BaseModel):
    recording_id: int
    status: str  # "validated" | "rejected" | "recorded"
    review_notes: str = ""

@app.post("/api/audio/status")
def update_clip_status(payload: ClipStatusUpdatePayload):
    """Validate or reject an uploaded audio clip."""
    ok = update_audio_recording_status(payload.recording_id, payload.status, payload.review_notes)
    if not ok:
        return JSONResponse(status_code=404, content={"status": "ERROR", "error": "Enregistrement non trouvé"})
    return {"status": "SUCCESS", "recording_id": payload.recording_id, "new_status": payload.status}

# --- Agro-Climatic Zones & Stochastic Simulation (Step E2) ---

@app.get("/api/weather/zones")
def get_zones():
    """List 5 agro-climatic zones of Togo with regional normals, regimes and sentinel village soils."""
    zones = list_zone_profiles()
    return [z.model_dump() for z in zones]

@app.get("/api/weather/zones/{zone_id}")
def get_zone_detail(zone_id: str):
    """Retrieve detailed climate and soil parameters for a specific zone."""
    zp = get_zone_profile(zone_id)
    if not zp:
        return JSONResponse(status_code=404, content={"status": "ERROR", "error": f"Zone '{zone_id}' non trouvée"})
    return zp.model_dump()

class SimulateSeasonsPayload(BaseModel):
    zone_id: str
    n_seasons: int = 30
    seed: Optional[int] = 42

@app.post("/api/weather/simulate-seasons")
def simulate_seasons(payload: SimulateSeasonsPayload):
    """Run stochastic Markov-Gamma simulation for N seasons for a given zone."""
    zp = get_zone_profile(payload.zone_id)
    if not zp:
        return JSONResponse(status_code=404, content={"status": "ERROR", "error": f"Zone '{payload.zone_id}' non trouvée"})

    gen = StochasticWeatherGenerator(zp, seed=payload.seed)
    summary = gen.simulate_n_seasons(n_seasons=max(1, min(100, payload.n_seasons)))

    return {
        "zone_id": summary.zone_id,
        "zone_name": summary.zone_name,
        "seasons_count": summary.seasons_count,
        "mean_annual_rainfall_mm": summary.mean_annual_rainfall_mm,
        "std_annual_rainfall_mm": summary.std_annual_rainfall_mm,
        "mean_rain_days": summary.mean_rain_days,
        "false_start_rate_pct": summary.false_start_rate_pct,
        "median_onset_day_of_year": summary.median_onset_day_of_year,
        "median_onset_date_str": summary.median_onset_date_str
    }

# --- Agro-Water Balance & Sowing Window (Step E3) ---

@app.get("/api/agro/water-balance")
def get_water_balance(village_id: str = Query(..., description="Pcode ou identifiant du village"), crop: str = "mais"):
    """Root-zone soil water balance, ET0, and 21-day false start risk evaluation."""
    v = repo.get_village(village_id)
    if not v:
        return JSONResponse(status_code=404, content={"status": "ERROR", "error": f"Village '{village_id}' non trouvé"})

    soil = repo.get_soil_for_village(v.village_id)
    weather = precompute_engine.weather_service.get_weather_for_village(v)

    taw_m = soil.taw_mm_m if soil else 100.0
    depth = soil.depth_cm if soil else 100.0
    today_doy = date.today().timetuple().tm_yday
    tmin = weather.daily_forecast_tmin[0] if weather.daily_forecast_tmin else 22.0
    tmax = weather.daily_forecast_tmax[0] if weather.daily_forecast_tmax else 33.0
    daily_et0 = calculate_hargreaves_samani_et0(tmin, tmax, v.latitude, today_doy)

    res = SoilWaterReservoir(
        taw_mm_m=taw_m,
        depth_cm=depth,
        initial_fill_fraction=min(1.0, max(0.25, weather.rain_last_3days_mm / max(10.0, taw_m * (depth / 100.0))))
    )

    # 21-day seedling stress simulation
    post_eval = simulate_post_sowing_21days(
        reservoir=res,
        daily_rain=weather.daily_forecast_rain,
        daily_tmax=weather.daily_forecast_tmax,
        daily_tmin=weather.daily_forecast_tmin,
        latitude_deg=v.latitude,
        start_doy=today_doy
    )

    sufficient_for_sowing = (res.soil_moisture_pct >= 25.0) and (not post_eval["is_false_start_risk"])

    return {
        "village_id": v.village_id,
        "village_name": v.village_name,
        "region": v.region,
        "soil_texture": soil.texture if soil else "standard",
        "taw_mm": res.taw_mm,
        "current_water_mm": res.current_water_mm,
        "soil_moisture_pct": res.soil_moisture_pct,
        "is_at_wilting_point": res.is_at_wilting_point,
        "daily_et0_mm": daily_et0,
        "sufficient_for_sowing": sufficient_for_sowing,
        "post_sowing_21d_false_start_risk": post_eval["is_false_start_risk"],
        "post_sowing_min_moisture_pct": post_eval["min_soil_moisture_pct"],
        "max_consecutive_wilting_days": post_eval["max_consecutive_wilting_days"],
        "details": f"Sol {soil.texture if soil else 'standard'} : TAW={res.taw_mm}mm, Humidité={res.soil_moisture_pct:.0f}%"
    }

@app.get("/api/agro/sowing-window")
def get_sowing_window(village_id: str = Query(...), crop: str = "mais", variety_id: Optional[str] = None):
    """Ideal sowing window by crop and variety, bounded by cessation of rains."""
    v = repo.get_village(village_id)
    if not v:
        return JSONResponse(status_code=404, content={"status": "ERROR", "error": f"Village '{village_id}' non trouvé"})

    soil = repo.get_soil_for_village(v.village_id)
    try:
        crop_enum = CropType(crop.lower())
    except ValueError:
        crop_enum = CropType.MAIS

    varieties = repo.list_varieties_for_crop(crop_enum)
    if not varieties:
        return JSONResponse(status_code=404, content={"status": "ERROR", "error": f"Aucune variété pour la culture '{crop}'"})

    selected_var = next((var for var in varieties if var.variety_id == variety_id), varieties[0])
    zp = get_zone_profile(v.region.upper())

    window = calculate_sowing_window(
        village=v,
        variety=selected_var,
        zone_profile=zp,
        current_soil=soil
    )
    return window.model_dump()

# --- Frontend Views ---

@app.get("/", response_class=RedirectResponse)
def root_redirect():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_view():
    """PWA Dashboard for Cooperatives, ICAT/ITRA Agents and Hackathon Jury."""
    from src.dashboard.views import render_dashboard_html
    return render_dashboard_html()

@app.get("/ussd-simulator", response_class=HTMLResponse)
def ussd_simulator_view():
    """Interactive 2G Feature Phone Simulator (GSM 03.38 USSD & Voice playback)."""
    from src.dashboard.views import render_simulator_html
    return render_simulator_html()

@app.get("/audio-recorder", response_class=HTMLResponse)
def audio_recorder_view():
    """Web studio for native speaker audio recording and validation (Step E1)."""
    from src.dashboard.views import render_audio_recorder_html
    return render_audio_recorder_html()

@app.get("/zones-overview", response_class=HTMLResponse)
def zones_overview_view():
    """Visual overview of the 5 agro-climatic zones and stochastic simulator (Step E2)."""
    from src.dashboard.views import render_zones_overview_html
    return HTMLResponse(content=render_zones_overview_html())

class AudioEvaluationPayload(BaseModel):
    clip_id: str
    language: str
    clarity_rating: int
    naturalness_rating: int
    accent_authenticity_rating: int
    comprehension_check_passed: bool = True
    evaluator_name: Optional[str] = "Anonyme"
    evaluator_origin_region: Optional[str] = "Maritime"
    comments: Optional[str] = ""

@app.get("/audio-eval", response_class=HTMLResponse)
def audio_eval_view():
    """Native speaker audio evaluation studio and metrics dashboard (Step E10)."""
    from src.dashboard.views import render_audio_eval_html
    return HTMLResponse(content=render_audio_eval_html())

@app.post("/api/audio-eval")
def submit_audio_evaluation(payload: AudioEvaluationPayload):
    """Save an evaluation score from a native speaker or jury member (Step E10)."""
    eval_id = save_audio_evaluation(
        clip_id=payload.clip_id,
        language=payload.language,
        clarity_rating=payload.clarity_rating,
        naturalness_rating=payload.naturalness_rating,
        accent_authenticity_rating=payload.accent_authenticity_rating,
        comprehension_check_passed=payload.comprehension_check_passed,
        evaluator_name=payload.evaluator_name,
        evaluator_origin_region=payload.evaluator_origin_region,
        comments=payload.comments
    )
    record_event(
        event_type="audio_eval",
        village_id=payload.evaluator_origin_region or "Maritime",
        channel="WEB",
        payload={
            "eval_id": eval_id,
            "language": payload.language,
            "clip_id": payload.clip_id,
            "clarity": payload.clarity_rating,
            "naturalness": payload.naturalness_rating,
            "accent": payload.accent_authenticity_rating,
            "comprehension": payload.comprehension_check_passed
        },
        phone_hash=f"eval_{eval_id}"
    )
    return {
        "status": "SUCCESS",
        "evaluation_id": eval_id,
        "message": f"Évaluation enregistrée pour {payload.language} (ID {eval_id})"
    }

@app.get("/api/audio-eval/summary")
def get_audio_eval_summary():
    """Get aggregated metrics per language and overall (Step E10)."""
    return get_audio_evaluations_summary()

@app.get("/api/audio-eval/list")
def list_audio_evals(language: Optional[str] = None):
    """List recent audio evaluations (Step E10)."""
    return list_audio_evaluations(language=language)


