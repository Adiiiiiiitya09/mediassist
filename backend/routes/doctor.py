from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

from models.db_models import User, Consultation, Message, Report, DoctorProfile, PatientProfile, ConsultStatus
from models.schemas import DoctorApproval, DoctorReject, DoctorProfileUpdate
from routes.auth import verify_firebase_token
from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


def require_doctor(decoded: dict = Depends(verify_firebase_token), db: Session = Depends(get_db)):
    if decoded.get('role') != 'doctor':
        raise HTTPException(status_code=403, detail='Forbidden')
    user = db.query(User).filter(User.firebase_uid == decoded['uid']).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user


# ── Profile ───────────────────────────────────────────────────────────────────
@router.get('/profile')
async def get_profile(doctor=Depends(require_doctor), db: Session = Depends(get_db)):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()
    return {
        'name': doctor.name, 'email': doctor.email,
        'specialization': profile.specialization if profile else None,
        'qualification': profile.qualification if profile else None,
        'experience_years': profile.experience_years if profile else None,
        'license_number': profile.license_number if profile else None,
        'hospital': profile.hospital if profile else None,
        'department': profile.department if profile else None,
        'phone': profile.phone if profile else None,
        'bio': profile.bio if profile else None,
    }

@router.put('/profile')
async def update_profile(data: DoctorProfileUpdate, doctor=Depends(require_doctor), db: Session = Depends(get_db)):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor.id).first()
    if not profile:
        profile = DoctorProfile(user_id=doctor.id)
        db.add(profile)
    for k, v in data.dict(exclude_none=True).items():
        setattr(profile, k, v)
    db.commit()
    return {'message': 'Profile updated'}


# ── Dashboard ─────────────────────────────────────────────────────────────────
@router.get('/pending')
async def get_pending(doctor=Depends(require_doctor), db: Session = Depends(get_db)):
    consults = db.query(Consultation).filter(
        Consultation.status == ConsultStatus.pending,
        Consultation.interview_complete == 1
    ).order_by(Consultation.created_at.desc()).all()

    result = []
    for c in consults:
        patient = db.query(User).filter(User.id == c.patient_id).first()
        report = db.query(Report).filter(Report.consultation_id == c.id).first()
        chief = 'Consultation'
        if report and report.structured_json:
            try:
                chief = json.loads(report.structured_json).get('chief_complaint', 'Consultation')
            except:
                pass
        result.append({
            'consultation_id': c.id,
            'patient_name': patient.name if patient else 'Unknown',
            'chief_complaint': chief,
            'confidence_score': report.confidence_score if report else None,
            'confidence_tier': report.confidence_tier if report else None,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        })
    return result


@router.get('/consultation/{consultation_id}')
async def get_consultation(consultation_id: int, doctor=Depends(require_doctor), db: Session = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail='Not found')

    patient = db.query(User).filter(User.id == consult.patient_id).first()
    patient_profile = db.query(PatientProfile).filter(PatientProfile.user_id == consult.patient_id).first()
    report = db.query(Report).filter(Report.consultation_id == consult.id).first()
    messages = db.query(Message).filter(Message.consultation_id == consult.id).order_by(Message.timestamp).all()

    structured = json.loads(report.structured_json) if report and report.structured_json else {}
    prediction = json.loads(report.prediction_json) if report and report.prediction_json else {}

    return {
        'consultation_id': consult.id,
        'status': consult.status.value,
        'patient_name': patient.name if patient else 'Unknown',
        'patient_profile': {
            'age': patient_profile.age if patient_profile else None,
            'gender': patient_profile.gender if patient_profile else None,
            'blood_group': patient_profile.blood_group if patient_profile else None,
            'known_allergies': patient_profile.known_allergies if patient_profile else None,
            'current_medications': patient_profile.current_medications if patient_profile else None,
            'chronic_conditions': patient_profile.chronic_conditions if patient_profile else None,
        },
        'structured_data': structured,
        'prediction': prediction,
        'confidence_score': report.confidence_score if report else None,
        'confidence_tier': report.confidence_tier if report else None,
        'doctor_notes': report.doctor_notes if report else None,
        'prescription': report.prescription if report else None,
        'transcript': [{'role': m.role, 'content': m.content} for m in messages],
    }


# ── Approve / Reject ──────────────────────────────────────────────────────────
@router.post('/approve/{consultation_id}')
async def approve(consultation_id: int, data: DoctorApproval, doctor=Depends(require_doctor), db: Session = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail='Not found')

    consult.status = ConsultStatus.approved
    consult.doctor_id = doctor.id

    report = db.query(Report).filter(Report.consultation_id == consultation_id).first()
    if report:
        report.doctor_notes = data.notes
        report.prescription = data.prescription
        report.approved_at = datetime.utcnow()

    db.commit()
    return {'message': 'Consultation approved'}


@router.post('/reject/{consultation_id}')
async def reject(consultation_id: int, data: DoctorReject, doctor=Depends(require_doctor), db: Session = Depends(get_db)):
    consult = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail='Not found')

    consult.status = ConsultStatus.rejected
    consult.doctor_id = doctor.id

    report = db.query(Report).filter(Report.consultation_id == consultation_id).first()
    if report:
        report.doctor_notes = data.notes

    db.commit()
    return {'message': 'Consultation rejected'}