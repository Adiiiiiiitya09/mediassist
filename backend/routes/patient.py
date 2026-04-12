from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
from models.schemas import PatientProfileUpdate
from firebase_config import get_firestore_client
from routes.auth import verify_firebase_token

router = APIRouter()

def get_firestore():
    return get_firestore_client()

def require_patient(decoded_token: dict = Depends(verify_firebase_token)):
    """Ensure the user has patient role."""
    if decoded_token.get('role') != 'patient':
        raise HTTPException(status_code=403, detail='Forbidden - Patient access required')
    return decoded_token['uid']


# ──────────────────────────────────────────────────────────────
# PROFILE ENDPOINTS
# ──────────────────────────────────────────────────────────────

@router.get('/profile')
async def get_profile(user_id: str = Depends(require_patient), db=Depends(get_firestore)):
    """
    Returns the patient's full profile including user info and medical background.
    
    Returns: name, email, role, created_at, and all patient_profile fields
    """
    try:
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail='Profile not found')

        user_data = user_doc.to_dict()
        profile = user_data.get('patient_profile', {})
        profile.update({
            'name': user_data.get('name'),
            'email': user_data.get('email'),
            'role': user_data.get('role'),
            'created_at': user_data.get('created_at')
        })
        return profile

    except HTTPException:
        raise
    except Exception as e:
        print(f"Get patient profile error: {e}")
        raise HTTPException(status_code=500, detail='Failed to get profile')


@router.put('/profile')
async def update_profile(
    profile_data: PatientProfileUpdate,
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    """
    Updates the patient's medical profile data.
    Only updates patient_profile nested document - account fields stay unchanged.
    
    Accepts: age, gender, blood_group, height_cm, weight_kg, chronic_conditions,
             past_surgeries, current_medications, known_allergies, family_history,
             smoking, alcohol, exercise, emergency_contact_name, emergency_contact_phone
    """
    try:
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail='Profile not found')

        # Filter to only patient profile fields
        patient_fields = [
            'age', 'gender', 'blood_group', 'height_cm', 'weight_kg',
            'chronic_conditions', 'past_surgeries', 'current_medications',
            'known_allergies', 'family_history', 'smoking', 'alcohol',
            'exercise', 'emergency_contact_name', 'emergency_contact_phone'
        ]
        patient_profile = {k: v for k, v in profile_data.dict().items() if k in patient_fields and v is not None}

        db.collection('users').document(user_id).update({
            'patient_profile': patient_profile,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        return {'message': 'Profile updated successfully'}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Update patient profile error: {e}")
        raise HTTPException(status_code=500, detail='Failed to update profile')
