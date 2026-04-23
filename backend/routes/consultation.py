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
        if consult.interview_complete == 1:
            raise HTTPException(status_code=400, detail='Interview already complete. No more messages allowed.')

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

        # If interview done: mark complete first, then try scribe + ML
        if is_complete:
            consult.interview_complete = 1
            db.commit()

            try:
                structured = extract_structured_data(history)
                prediction = predict(structured, structured.get('interview_quality', 'medium'))

                db.add(Report(
                    consultation_id=consult.id,
                    structured_json=json.dumps(structured),
                    prediction_json=json.dumps(prediction),
                    confidence_score=prediction['score'],
                    confidence_tier=prediction['tier'],
                ))
                db.commit()
            except Exception as report_err:
                logger.error(f"Report generation failed for consultation {consult.id}: {report_err}", exc_info=True)
                # Still mark complete — the rescue_cases script or a retry can fill in the report later
                db.rollback()
                # Re-assert interview_complete since rollback may have reverted it
                consult = db.query(Consultation).filter(Consultation.id == body.consultation_id).first()
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
            'has_doctor_response': report.doctor_notes is not None if report else False,
        })
    return result


# ── Delete Consultation ───────────────────────────────────────────────────────
@router.delete('/{consultation_id}')
async def delete_consultation(consultation_id: int, patient=Depends(require_patient), db: Session = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail='Consultation not found')
    if consult.patient_id != patient.id:
        raise HTTPException(status_code=403, detail='Forbidden')
    
    try:
        # Delete related entities
        db.query(Message).filter(Message.consultation_id == consult.id).delete()
        db.query(Report).filter(Report.consultation_id == consult.id).delete()
        db.delete(consult)
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting consultation: {e}")
        raise HTTPException(status_code=500, detail='Failed to delete consultation')


# ── Get Report ────────────────────────────────────────────────────────────────
@router.get('/report/{consultation_id}')
async def get_report(consultation_id: int, patient=Depends(require_patient), db: Session = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail='Consultation not found')
    if consult.patient_id != patient.id:
        raise HTTPException(status_code=403, detail='Forbidden')

    report = db.query(Report).filter(Report.consultation_id == consult.id).first()
    messages = db.query(Message).filter(Message.consultation_id == consult.id).order_by(Message.timestamp).all()
    transcript = [{'role': m.role, 'content': m.content} for m in messages]

    data = {
        'consultation_id': consult.id,
        'status': consult.status.value,
        'created_at': consult.created_at.isoformat() if consult.created_at else None,
        'transcript': transcript,
        'chief_complaint': 'Consultation',
        'vital_flags': [],
        'medical_history': [],
        'current_medications': [],
        'allergies': [],
        'symptoms': [],
        'associated_symptoms': [],
        'doctor_notes': report.doctor_notes if report else None,
        'prescription': report.prescription if report else None,
        'approved_at': report.approved_at.isoformat() if report and report.approved_at else None,
        'confidence_score': report.confidence_score if report else None,
        'confidence_tier': report.confidence_tier if report else None,
    }

    if report and report.structured_json:
        try:
            struct = json.loads(report.structured_json)
            data['chief_complaint'] = struct.get('chief_complaint', 'Consultation')
            data['vital_flags'] = struct.get('vital_flags', [])
            data['medical_history'] = struct.get('medical_history', [])
            data['current_medications'] = struct.get('current_medications', [])
            data['allergies'] = struct.get('allergies', [])
            data['symptoms'] = struct.get('symptoms', [])
            data['associated_symptoms'] = struct.get('associated_symptoms', [])
        except json.JSONDecodeError:
            pass

    return data


# ── Download Report ───────────────────────────────────────────────────────────
@router.get('/download-report/{consultation_id}')
async def download_report(consultation_id: int, patient=Depends(require_patient), db: Session = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail='Consultation not found')
    if consult.patient_id != patient.id:
        raise HTTPException(status_code=403, detail='Forbidden')

    report = db.query(Report).filter(Report.consultation_id == consult.id).first()
    if not report or not report.structured_json:
        raise HTTPException(status_code=400, detail='Report not available yet')

    try:
        struct = json.loads(report.structured_json)
    except:
        struct = {}

    content = f"MEDICAL CONSULTATION REPORT\n"
    content += f"===========================\n"
    content += f"Case ID: {consult.id}\n"
    content += f"Date: {consult.created_at.strftime('%Y-%m-%d %H:%M') if consult.created_at else ''}\n"
    content += f"Patient: {patient.name}\n"
    content += f"Status: {consult.status.value.upper()}\n\n"
    
    content += f"CHIEF COMPLAINT\n---------------\n"
    content += f"{struct.get('chief_complaint', 'N/A')}\n\n"
    
    if struct.get('vital_flags'):
        content += f"VITAL FLAGS\n-----------\n"
        for flag in struct.get('vital_flags', []):
            content += f"  ! {flag}\n"
        content += "\n"

    content += f"SYMPTOMS\n--------\n"
    for s in struct.get('symptoms', []):
        content += f"- {s.get('name', 'Unknown')}\n"
        if s.get('severity'): content += f"  Severity: {s.get('severity')}/10\n"
        if s.get('duration'): content += f"  Duration: {s.get('duration')}\n"
    if struct.get('associated_symptoms'):
        content += f"Associated: {', '.join(struct.get('associated_symptoms'))}\n"
    content += "\n"

    if report.doctor_notes:
        content += f"DOCTOR'S NOTES\n--------------\n"
        content += f"{report.doctor_notes}\n\n"
    
    if report.prescription:
        content += f"PRESCRIPTION\n------------\n"
        content += f"{report.prescription}\n\n"

    return {
        'content': content,
        'filename': f'mediassist_report_{consult.id}.txt'
    }


# ── Reconsult ─────────────────────────────────────────────────────────────────
@router.post('/reconsult/{consultation_id}')
async def reconsult(consultation_id: int, patient=Depends(require_patient), db: Session = Depends(get_db)):
    old_consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not old_consult:
        raise HTTPException(status_code=404, detail='Consultation not found')
    if old_consult.patient_id != patient.id:
        raise HTTPException(status_code=403, detail='Forbidden')
        
    try:
        new_consult = Consultation(patient_id=patient.id)
        db.add(new_consult)
        db.commit()
        db.refresh(new_consult)
        
        # We don't copy messages, the frontend handles context or restarts.
        return {'consultation_id': new_consult.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Reconsult error: {e}")
        raise HTTPException(status_code=500, detail='Failed to start reconsultation')