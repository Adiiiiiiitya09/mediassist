from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.db_models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./telehealth.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
Base.metadata.create_all(bind=engine)

app = FastAPI(title='MediAssist Telehealth API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

from routes import auth, consultation, doctor

app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(consultation.router, prefix='/consultation', tags=['consultation'])
app.include_router(doctor.router, prefix='/doctor', tags=['doctor'])

@app.get('/')
async def root():
    return {'message': 'MediAssist Telehealth API'}
