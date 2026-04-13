from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# ── Database setup ────────────────────────────────────────────────────────────
from database import engine
from models.db_models import Base
Base.metadata.create_all(bind=engine)
logger.info("✓ Database tables created/verified")

# ── Firebase Auth only (no Firestore) ─────────────────────────────────────────
from firebase_config import initialize_firebase
try:
    initialize_firebase()
    logger.info("✓ Firebase initialized")
except Exception as e:
    logger.error(f"✗ Firebase init failed: {e}")
    raise

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title='MediAssist Telehealth API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

from routes import auth, consultation, doctor, patient
app.include_router(auth.router,         prefix='/auth',         tags=['auth'])
app.include_router(consultation.router, prefix='/consultation', tags=['consultation'])
app.include_router(doctor.router,       prefix='/doctor',       tags=['doctor'])
app.include_router(patient.router,      prefix='/patient',      tags=['patient'])

@app.get('/')
async def root():
    return {'message': 'MediAssist API running'}