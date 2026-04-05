from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json
from typing import Optional
from datetime import datetime
from models.db_models import Consultation, Message, Report, User, ConsultStatus, Base
from models.schemas import ConsultationStart, MessageRequest, MessageResponse, ConsultationStatus
from services.ai_interview import get_ai_response
from services.scribe import extract_structured_data
from services.predictor import predict
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

def require_patient(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='No token provided')
    
    token = authorization.replace('Bearer ', '')
    payload = decode_token(token)
    
    if not payload or payload.get('role') != 'patient':
        raise HTTPException(status_code=403, detail='Forbidden')
    
    return payload['user_id']

@router.post('/start')
async def start_consultation(user_id: int = Depends(require_patient), db: Session = Depends(get_db)):
    consultation = Consultation(patient_id=user_id, status=ConsultStatus.pending)
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    
    return {'consultation_id': consultation.id}

@router.post('/message', response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    user_id: int = Depends(require_patient),
    db: Session = Depends(get_db)
):
    # Save patient message
    db.add(Message(consultation_id=body.consultation_id, role='user', content=body.message))
    db.commit()
    
    # Load full history
    msgs = db.query(Message).filter(Message.consultation_id == body.consultation_id).order_by(Message.timestamp).all()
    history = [{'role': m.role, 'content': m.content} for m in msgs]
    
    # Get AI reply
    reply, is_complete = get_ai_response(history)
    
    # Save AI reply
    db.add(Message(consultation_id=body.consultation_id, role='assistant', content=reply))
    db.commit()
    
    # If done: run scribe + predictor, save Report
    if is_complete:
        structured = extract_structured_data(history)
        symptoms = [s['name'] for s in structured.get('symptoms', [])]
        symptoms += structured.get('associated_symptoms', [])
        
        prediction = predict(symptoms, structured.get('interview_quality', 'medium'))
        
        db.add(Report(
            consultation_id=body.consultation_id,
            structured_json=json.dumps(structured),
            prediction_json=json.dumps(prediction),
            confidence_score=prediction['score'],
            confidence_tier=prediction['tier']
        ))
        
        consult = db.query(Consultation).get(body.consultation_id)
        consult.interview_complete = 1
        db.commit()
    
    # ⚠️ ETHICAL RULE: return only reply + is_complete – NO disease data to patient
    return {'reply': reply, 'is_complete': is_complete}

@router.get('/status/{consultation_id}', response_model=ConsultationStatus)
async def check_status(
    consultation_id: int,
    user_id: int = Depends(require_patient),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).get(consultation_id)
    
    if not consultation or consultation.patient_id != user_id:
        raise HTTPException(status_code=404, detail='Consultation not found')
    
    return {
        'id': consultation.id,
        'status': consultation.status.value,
        'interview_complete': consultation.interview_complete
    }
