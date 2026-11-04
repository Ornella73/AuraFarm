"""FastAPI Application for AuraFarm: Telecom Webhooks, PWA Dashboard, and 2G Phone Simulator."""
import os
from datetime import datetime, date, timezone
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Form, Response, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
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
    get_freshness_status
)
from src.data_ingestion.repositories import SpatialRepository
from src.data_ingestion.precompute_engine import PrecomputeEngine
from src.alerts.backtest import BacktestEngine
from src.channels.ussd_engine import UssdSessionEngine
from src.channels.voice_ivr import VoiceIvrEngine
from src.channels.missed_call import MissedCallHandler
from src.channels.sms_handler import SmsHandler
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
