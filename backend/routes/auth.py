from fastapi import APIRouter, Depends, HTTPException, Header
from firebase_admin import auth as firebase_auth
from sqlalchemy.orm import Session
from typing import Optional
import logging

from models.db_models import User, PatientProfile, DoctorProfile, UserRole
from models.schemas import PatientRegister, UserLogin
from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Token verification (shared by all protected routes) ───────────────────────
def verify_firebase_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='No token provided')

    id_token = authorization.replace('Bearer ', '')
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded['uid']

        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        decoded['role'] = user.role.value
        return decoded
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail='Invalid or expired token')


# ── Register ──────────────────────────────────────────────────────────────────
@router.post('/register')
async def register(body: PatientRegister, db: Session = Depends(get_db)):
    logger.info(f"Register: {body.email}, role: {body.role}")

    if not body.firebase_uid:
        raise HTTPException(status_code=400, detail='firebase_uid is required')
    if body.role not in ['patient', 'doctor']:
        raise HTTPException(status_code=400, detail='Invalid role')

    existing = db.query(User).filter(User.firebase_uid == body.firebase_uid).first()
    if existing:
        raise HTTPException(status_code=409, detail='User already registered')

    try:
        user = User(
            firebase_uid=body.firebase_uid,
            name=body.name,
            email=body.email,
            role=UserRole(body.role),
        )
        db.add(user)
        db.flush()

        if body.role == 'patient':
            db.add(PatientProfile(
                user_id=user.id,
                age=body.age,
                gender=body.gender,
                blood_group=body.blood_group,
                height_cm=body.height_cm,
                weight_kg=body.weight_kg,
                chronic_conditions=body.chronic_conditions,
                past_surgeries=body.past_surgeries,
                current_medications=body.current_medications,
                known_allergies=body.known_allergies,
                family_history=body.family_history,
                smoking=body.smoking,
                alcohol=body.alcohol,
                exercise=body.exercise,
                emergency_contact_name=body.emergency_contact_name,
                emergency_contact_phone=body.emergency_contact_phone,
            ))
        elif body.role == 'doctor':
            db.add(DoctorProfile(user_id=user.id))

        db.commit()
        logger.info(f"Registered: {body.firebase_uid}")
        return {'message': 'Registered successfully', 'uid': body.firebase_uid, 'role': body.role}

    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f'Registration failed: {str(e)}')


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post('/login')
async def login(body: UserLogin, db: Session = Depends(get_db)):
    if not body.firebase_token:
        raise HTTPException(status_code=400, detail='firebase_token is required')

    try:
        decoded = firebase_auth.verify_id_token(body.firebase_token)
        uid = decoded['uid']
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid token')

    user = db.query(User).filter(User.firebase_uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found. Please register first.')

    return {'message': 'Login successful', 'uid': uid, 'role': user.role.value, 'name': user.name}


# ── Verify ────────────────────────────────────────────────────────────────────
@router.get('/verify')
async def verify_token(decoded: dict = Depends(verify_firebase_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.firebase_uid == decoded['uid']).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return {'uid': decoded['uid'], 'role': user.role.value, 'email': user.email, 'name': user.name}