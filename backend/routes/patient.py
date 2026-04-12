from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from models.db_models import User, PatientProfile
from models.schemas import PatientProfileUpdate
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


@router.get('/profile')
async def get_profile(patient=Depends(require_patient), db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    return {
        'name': patient.name,
        'email': patient.email,
        'age': profile.age if profile else None,
        'gender': profile.gender if profile else None,
        'blood_group': profile.blood_group if profile else None,
        'height_cm': profile.height_cm if profile else None,
        'weight_kg': profile.weight_kg if profile else None,
        'chronic_conditions': profile.chronic_conditions if profile else None,
        'past_surgeries': profile.past_surgeries if profile else None,
        'current_medications': profile.current_medications if profile else None,
        'known_allergies': profile.known_allergies if profile else None,
        'family_history': profile.family_history if profile else None,
        'smoking': profile.smoking if profile else None,
        'alcohol': profile.alcohol if profile else None,
        'exercise': profile.exercise if profile else None,
        'emergency_contact_name': profile.emergency_contact_name if profile else None,
        'emergency_contact_phone': profile.emergency_contact_phone if profile else None,
    }


@router.put('/profile')
async def update_profile(data: PatientProfileUpdate, patient=Depends(require_patient), db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    if not profile:
        profile = PatientProfile(user_id=patient.id)
        db.add(profile)
    for k, v in data.dict(exclude_none=True).items():
        setattr(profile, k, v)
    db.commit()
    return {'message': 'Profile updated'}