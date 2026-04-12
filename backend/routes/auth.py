from fastapi import APIRouter, Depends, HTTPException, Header
from firebase_admin import auth as firebase_auth, firestore
from typing import Optional
from models.schemas import PatientRegister, DoctorRegister, UserLogin
from firebase_config import get_firestore_client

router = APIRouter()

def get_firestore():
    return get_firestore_client()

# ──────────────────────────────────────────────────────────────
# Token Verification (used by ALL protected routes)
# ──────────────────────────────────────────────────────────────
def verify_firebase_token(authorization: Optional[str] = Header(None), db=Depends(get_firestore)):
    """
    Verifies the Firebase ID token from the Authorization header.
    Returns the decoded token dict with uid and role from Firestore.
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='No token provided')

    id_token = authorization.replace('Bearer ', '')

    try:
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded['uid']
        
        # Get user document from Firestore
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail='User not found')
        
        user_data = user_doc.to_dict()
        decoded['role'] = user_data.get('role')
        return decoded
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid or expired token')


# ──────────────────────────────────────────────────────────────
# REGISTER
# ──────────────────────────────────────────────────────────────
@router.post('/register')
async def register(body: PatientRegister, db=Depends(get_firestore)):
    """
    Registration flow:
    1. Frontend already created the user in Firebase Auth and got an ID token
    2. Frontend calls this endpoint with the firebase_uid + profile data
    3. We create the user record and profile in Firestore
    4. Stores both user info and profile data in single document
    
    For patients: Stores age, gender, blood_group, health info, emergency contact, etc.
    For doctors: Stores specialization, qualification, experience, license, hospital, etc.
    """
    if not body.firebase_uid:
        raise HTTPException(status_code=400, detail='firebase_uid is required')

    # Check if user already exists in Firestore
    user_doc = db.collection('users').document(body.firebase_uid).get()
    if user_doc.exists:
        raise HTTPException(status_code=400, detail='User already registered')

    # Validate role
    if body.role not in ['patient', 'doctor']:
        raise HTTPException(status_code=400, detail='Invalid role. Use patient or doctor')

    try:
        # Create user document in Firestore
        user_data = {
            'uid': body.firebase_uid,
            'name': body.name,
            'email': body.email,
            'role': body.role,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }

        # Add role-specific profile data
        if body.role == 'patient':
            user_data['patient_profile'] = {
                'age': body.age,
                'gender': body.gender,
                'blood_group': body.blood_group,
                'height_cm': body.height_cm,
                'weight_kg': body.weight_kg,
                'chronic_conditions': body.chronic_conditions,
                'past_surgeries': body.past_surgeries,
                'current_medications': body.current_medications,
                'known_allergies': body.known_allergies,
                'family_history': body.family_history,
                'smoking': body.smoking,
                'alcohol': body.alcohol,
                'exercise': body.exercise,
                'emergency_contact_name': body.emergency_contact_name,
                'emergency_contact_phone': body.emergency_contact_phone
            }
        elif body.role == 'doctor':
            user_data['doctor_profile'] = {
                'specialization': body.specialization,
                'qualification': body.qualification,
                'experience_years': body.experience_years,
                'license_number': body.license_number,
                'hospital': body.hospital,
                'department': body.department,
                'phone': body.phone,
                'consultation_hours': body.consultation_hours,
                'bio': body.bio,
                'languages': body.languages
            }

        # Save to Firestore
        db.collection('users').document(body.firebase_uid).set(user_data)

        return {
            'message': 'Registered successfully',
            'uid': body.firebase_uid,
            'role': body.role
        }
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail='Registration failed')


# ──────────────────────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────────────────────
@router.post('/login')
async def login(body: UserLogin, db=Depends(get_firestore)):
    """
    Login flow:
    1. Frontend signs in with Firebase Auth and gets an ID token
    2. Frontend calls this endpoint with the ID token to verify in Firestore
    3. We verify the token and return the role for redirect
    
    Returns: uid, role, name (for redirect logic)
    """
    if not body.firebase_token:
        raise HTTPException(status_code=400, detail='firebase_token is required')

    try:
        decoded = firebase_auth.verify_id_token(body.firebase_token)
        uid = decoded['uid']
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid token')

    # Get user from Firestore
    user_doc = db.collection('users').document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail='User not found. Please register first.')

    user_data = user_doc.to_dict()
    return {
        'message': 'Login successful',
        'uid': uid,
        'role': user_data.get('role'),
        'name': user_data.get('name')
    }


# ──────────────────────────────────────────────────────────────
# VERIFY TOKEN
# ──────────────────────────────────────────────────────────────
@router.get('/verify')
async def verify_token(
    decoded: dict = Depends(verify_firebase_token),
    db=Depends(get_firestore)
):
    """
    Verifies the current auth state (used by frontend on page load).
    Returns the full user profile from Firestore.
    
    Requires: Authorization: Bearer {id_token} header
    """
    uid = decoded['uid']
    user_doc = db.collection('users').document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail='User not found')

    user_data = user_doc.to_dict()
    return {
        'uid': uid,
        'role': user_data.get('role'),
        'email': user_data.get('email'),
        'name': user_data.get('name'),
        'patient_profile': user_data.get('patient_profile'),
        'doctor_profile': user_data.get('doctor_profile')
    }
