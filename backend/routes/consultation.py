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

def require_doctor(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='No token provided')

    token = authorization.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload or payload.get('role') != 'doctor':
        raise HTTPException(status_code=403, detail='Forbidden')

    return payload['user_id']


# ─────────────────────────────────────────────
#  PATIENT ROUTES
# ─────────────────────────────────────────────

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
    msgs = db.query(Message).filter(
        Message.consultation_id == body.consultation_id
    ).order_by(Message.timestamp).all()
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


@router.get('/report/{consultation_id}')
async def get_patient_report(
    consultation_id: int,
    user_id: int = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """
    Called by the patient frontend after is_complete=true.
    Returns the ML prediction summary (no raw disease names — only
    confidence score/tier and the structured intake data).
    Actual top-5 diagnosis list is withheld from patients; doctors see it via /doctor/report.
    """
    consultation = db.query(Consultation).get(consultation_id)
    if not consultation or consultation.patient_id != user_id:
        raise HTTPException(status_code=404, detail='Consultation not found')

    if not consultation.interview_complete:
        raise HTTPException(status_code=400, detail='Interview not complete yet')

    report = db.query(Report).filter(
        Report.consultation_id == consultation_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail='Report not ready yet')

    structured = json.loads(report.structured_json)

    # ⚠️ Patients only see intake summary + confidence band, NOT the diagnosis list
    return {
        'consultation_id': consultation_id,
        'confidence_score': report.confidence_score,
        'confidence_tier': report.confidence_tier,
        'chief_complaint': structured.get('chief_complaint', ''),
        'symptoms': structured.get('symptoms', []),
        'associated_symptoms': structured.get('associated_symptoms', []),
        'vital_flags': structured.get('vital_flags', []),
        'medical_history': structured.get('medical_history', []),
        'current_medications': structured.get('current_medications', []),
        'allergies': structured.get('allergies', []),
        'message': 'Your intake report is ready. A doctor will review your case and provide a diagnosis shortly.'
    }


# ─────────────────────────────────────────────
#  DOCTOR ROUTES
# ─────────────────────────────────────────────

@router.get('/doctor/pending')
async def get_pending_consultations(
    doctor_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """Returns all consultations where interview is done but doctor hasn't reviewed yet."""
    consultations = db.query(Consultation).filter(
        Consultation.interview_complete == 1,
        Consultation.status == ConsultStatus.pending
    ).all()

    result = []
    for c in consultations:
        report = db.query(Report).filter(Report.consultation_id == c.id).first()
        result.append({
            'consultation_id': c.id,
            'patient_id': c.patient_id,
            'confidence_score': report.confidence_score if report else None,
            'confidence_tier': report.confidence_tier if report else None,
            'created_at': str(c.created_at) if hasattr(c, 'created_at') else None
        })

    return result


@router.get('/doctor/report/{consultation_id}')
async def get_doctor_report(
    consultation_id: int,
    doctor_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """
    Full report for the doctor — includes top-5 ML predictions,
    descriptions, precautions, and full structured intake.
    """
    report = db.query(Report).filter(
        Report.consultation_id == consultation_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail='Report not found')

    structured = json.loads(report.structured_json)
    prediction = json.loads(report.prediction_json)

    return {
        'consultation_id': consultation_id,
        'confidence_score': report.confidence_score,
        'confidence_tier': report.confidence_tier,
        'structured_intake': structured,
        'ml_prediction': prediction,   # full top5 with descriptions + precautions
    }


@router.post('/doctor/approve/{consultation_id}')
async def approve_consultation(
    consultation_id: int,
    doctor_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail='Not found')

    consultation.status = ConsultStatus.approved
    consultation.doctor_id = doctor_id
    db.commit()

    return {'message': 'Consultation approved', 'consultation_id': consultation_id}


@router.post('/doctor/reject/{consultation_id}')
async def reject_consultation(
    consultation_id: int,
    doctor_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail='Not found')

    consultation.status = ConsultStatus.rejected
    consultation.doctor_id = doctor_id
    db.commit()

    return {'message': 'Consultation rejected', 'consultation_id': consultation_id}