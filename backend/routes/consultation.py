from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json
import logging

from models.db_models import User, Consultation, Message, Report, ConsultStatus
from models.schemas import MessageRequest, MessageResponse, ConsultationStatus
from services.ai_interview import get_ai_response
from services.scribe import extract_structured_data
from services.predictor import predict
from routes.auth import verify_firebase_token
from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


def require_patient(decoded: dict = Depends(verify_firebase_token), db: Session = Depends(get_db)):
    if decoded.get('role') != 'patient':
        raise HTTPException(status_code=403, detail='Forbidden')
    user = db.query(User).filter(User.firebase_uid == decoded['uid']).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user


# ── Start consultation ────────────────────────────────────────────────────────
@router.post('/start')
async def start_consultation(patient=Depends(require_patient), db: Session = Depends(get_db)):
    try:
        consult = Consultation(patient_id=patient.id)
        db.add(consult)
        db.commit()
        db.refresh(consult)
        return {'consultation_id': consult.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Start consultation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail='Failed to start consultation')


# ── Send message ──────────────────────────────────────────────────────────────
@router.post('/message', response_model=MessageResponse)
async def send_message(body: MessageRequest, patient=Depends(require_patient), db: Session = Depends(get_db)):
    try:
        consult = db.query(Consultation).filter(Consultation.id == body.consultation_id).first()
        if not consult:
            raise HTTPException(status_code=404, detail='Consultation not found')
        if consult.patient_id != patient.id:
            raise HTTPException(status_code=403, detail='Forbidden')

        # Save patient message
        db.add(Message(consultation_id=consult.id, role='user', content=body.message))
        db.commit()

        # Build history for Claude
        messages = db.query(Message).filter(Message.consultation_id == consult.id).order_by(Message.timestamp).all()
        history = [{'role': m.role, 'content': m.content} for m in messages]

        # Get AI reply
        reply, is_complete = get_ai_response(history)

        # Save AI reply
        db.add(Message(consultation_id=consult.id, role='assistant', content=reply))
        db.commit()

        # If interview done: run scribe + ML, save report
        if is_complete:
            structured = extract_structured_data(history)
            symptoms = [s['name'] for s in structured.get('symptoms', [])]
            symptoms += structured.get('associated_symptoms', [])
            prediction = predict(symptoms, structured.get('interview_quality', 'medium'))

            db.add(Report(
                consultation_id=consult.id,
                structured_json=json.dumps(structured),
                prediction_json=json.dumps(prediction),
                confidence_score=prediction['score'],
                confidence_tier=prediction['tier'],
            ))
            consult.interview_complete = 1
            db.commit()

        # ⚠️ NEVER return disease data to patient
        return {'reply': reply, 'is_complete': is_complete}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Send message error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail='Failed to send message')


# ── Status ────────────────────────────────────────────────────────────────────
@router.get('/status/{consultation_id}')
async def check_status(consultation_id: int, patient=Depends(require_patient), db: Session = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail='Consultation not found')
    if consult.patient_id != patient.id:
        raise HTTPException(status_code=403, detail='Forbidden')
    return {'id': consult.id, 'status': consult.status.value, 'interview_complete': consult.interview_complete}


# ── History ───────────────────────────────────────────────────────────────────
@router.get('/history')
async def get_history(patient=Depends(require_patient), db: Session = Depends(get_db)):
    consults = db.query(Consultation).filter(Consultation.patient_id == patient.id).order_by(Consultation.created_at.desc()).all()
    result = []
    for c in consults:
        report = db.query(Report).filter(Report.consultation_id == c.id).first()
        chief = 'Consultation'
        if report and report.structured_json:
            try:
                chief = json.loads(report.structured_json).get('chief_complaint', 'Consultation')
            except:
                pass
        result.append({
            'consultation_id': c.id,
            'status': c.status.value,
            'interview_complete': c.interview_complete,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'chief_complaint': chief,
            'confidence_score': report.confidence_score if report else None,
            'confidence_tier': report.confidence_tier if report else None,
        })
    return result