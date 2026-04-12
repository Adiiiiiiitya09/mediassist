from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from firebase_config import initialize_firebase

load_dotenv()

# Initialize Firebase
initialize_firebase()

app = FastAPI(title='MediAssist Telehealth API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

from routes import auth, consultation, doctor, patient

app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(consultation.router, prefix='/consultation', tags=['consultation'])
app.include_router(doctor.router, prefix='/doctor', tags=['doctor'])
app.include_router(patient.router, prefix='/patient', tags=['patient'])

@app.get('/')
async def root():
    return {'message': 'MediAssist Telehealth API'}
