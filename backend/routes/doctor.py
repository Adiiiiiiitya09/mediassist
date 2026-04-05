from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json
from typing import Optional
from datetime import datetime
from models.db_models import Consultation, Report, User, ConsultStatus, Message, Base
from models.schemas import DoctorApproval, DoctorReject
from dotenv import load_dotenv
from routes.auth import decode_token

load_dotenv()

router = APIRouter()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./telehealth.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_doctor(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='No token provided')
    
    token = authorization.replace('Bearer ', '')
    payload = decode_token(token)
    
    if not payload or payload.get('role') != 'doctor':
        raise HTTPException(status_code=403, detail='Forbidden')
    
    return payload['user_id']

@router.get('/pending')
async def get_pending_consultations(user_id: int = Depends(require_doctor), db: Session = Depends(get_db)):
    consultations = db.query(Consultation).filter(
        Consultation.interview_complete == 1,
        Consultation.status == ConsultStatus.pending
    ).all()
    
    result = []
    for c in consultations:
        patient = db.query(User).get(c.patient_id)
        report = db.query(Report).filter(Report.consultation_id == c.id).first()
        
        result.append({
            'id': c.id,
            'patient_name': patient.name if patient else 'Unknown',
            'date': c.created_at.isoformat(),
            'urgency': report.confidence_tier if report else 'Unknown'
        })
    
    return result

@router.get('/consultation/{consultation_id}')
async def get_consultation_detail(
    consultation_id: int,
    user_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).get(consultation_id)
    
    if not consultation:
        raise HTTPException(status_code=404, detail='Consultation not found')
    
    patient = db.query(User).get(consultation.patient_id)
    report = db.query(Report).filter(Report.consultation_id == consultation_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail='Report not found')
    
    messages = db.query(Message).filter(Message.consultation_id == consultation_id).order_by(Message.timestamp).all()
    
    return {
        'id': consultation.id,
        'patient_name': patient.name if patient else 'Unknown',
        'patient_email': patient.email if patient else 'Unknown',
        'structured_data': json.loads(report.structured_json),
        'prediction': json.loads(report.prediction_json),
        'confidence_score': report.confidence_score,
        'confidence_tier': report.confidence_tier,
        'transcript': [{'role': m.role, 'content': m.content} for m in messages]
    }

@router.post('/approve/{consultation_id}')
async def approve_consultation(
    consultation_id: int,
    body: DoctorApproval,
    user_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).get(consultation_id)
    
    if not consultation:
        raise HTTPException(status_code=404, detail='Consultation not found')
    
    report = db.query(Report).filter(Report.consultation_id == consultation_id).first()
    
    if report:
        report.doctor_notes = body.notes
        report.prescription = body.prescription
        report.approved_at = datetime.utcnow()
    
    consultation.status = ConsultStatus.approved
    consultation.doctor_id = user_id
    db.commit()
    
    return {'message': 'Consultation approved'}

@router.post('/reject/{consultation_id}')
async def reject_consultation(
    consultation_id: int,
    body: DoctorReject,
    user_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).get(consultation_id)
    
    if not consultation:
        raise HTTPException(status_code=404, detail='Consultation not found')
    
    report = db.query(Report).filter(Report.consultation_id == consultation_id).first()
    
    if report:
        report.doctor_notes = body.notes
    
    consultation.status = ConsultStatus.rejected
    consultation.doctor_id = user_id
    db.commit()
    
    return {'message': 'Consultation rejected'}
