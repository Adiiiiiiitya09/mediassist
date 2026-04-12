from fastapi import APIRouter, Depends, HTTPException, Header
from firebase_admin import firestore
import os
import json
from typing import Optional
from datetime import datetime
from models.schemas import DoctorApproval, DoctorReject, DoctorProfileUpdate
from firebase_config import get_firestore_client
from routes.auth import verify_firebase_token

router = APIRouter()

def get_firestore():
    return get_firestore_client()

def require_doctor(decoded_token: dict = Depends(verify_firebase_token)):
    if decoded_token.get('role') != 'doctor':
        raise HTTPException(status_code=403, detail='Forbidden')
    return decoded_token['uid']


# ─────────────────────────────────────────────
#  DOCTOR PROFILE
# ─────────────────────────────────────────────

@router.get('/profile')
async def get_doctor_profile(user_id: str = Depends(require_doctor), db=Depends(get_firestore)):
    try:
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail='Profile not found')

        user_data = user_doc.to_dict()
        profile = user_data.get('doctor_profile', {})
        profile.update({
            'name': user_data.get('name'),
            'email': user_data.get('email'),
            'role': user_data.get('role'),
            'created_at': user_data.get('created_at')
        })
        return profile

    except Exception as e:
        print(f"Get doctor profile error: {e}")
        raise HTTPException(status_code=500, detail='Failed to get profile')

@router.put('/profile')
async def update_doctor_profile(
    profile_data: DoctorProfileUpdate,
    user_id: str = Depends(require_doctor),
    db=Depends(get_firestore)
):
    try:
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail='Profile not found')

        # Filter out non-doctor fields
        doctor_fields = [
            'specialization', 'qualification', 'experience_years', 'license_number',
            'hospital', 'department', 'phone', 'consultation_hours', 'bio', 'languages'
        ]
        doctor_profile = {k: v for k, v in profile_data.dict().items() if k in doctor_fields and v is not None}

        db.collection('users').document(user_id).update({
            'doctor_profile': doctor_profile,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        return {'message': 'Profile updated successfully'}

    except Exception as e:
        print(f"Update doctor profile error: {e}")
        raise HTTPException(status_code=500, detail='Failed to update profile')


# ─────────────────────────────────────────────
#  DOCTOR DASHBOARD
# ─────────────────────────────────────────────

@router.get('/dashboard')
async def get_doctor_dashboard(user_id: str = Depends(require_doctor), db=Depends(get_firestore)):
    try:
        # Get pending consultations (those without assigned doctors)
        pending_consultations = db.collection('consultations').where('status', '==', 'pending').where('doctor_id', '==', None).get()

        result = []
        for consultation in pending_consultations:
            consultation_data = consultation.to_dict()

            # Get patient info
            patient_doc = db.collection('users').document(consultation_data['patient_id']).get()
            patient_data = patient_doc.to_dict() if patient_doc.exists else {}

            # Get report if exists
            reports = db.collection('reports').where('consultation_id', '==', consultation.id).limit(1).get()
            report_data = None
            if reports:
                report_data = reports[0].to_dict()

            # Get chief complaint from structured data
            chief_complaint = 'Consultation'
            if report_data and report_data.get('structured_json'):
                try:
                    structured = json.loads(report_data['structured_json'])
                    chief_complaint = structured.get('chief_complaint', 'Consultation')
                except:
                    pass

            result.append({
                'consultation_id': consultation.id,
                'patient_name': patient_data.get('name', 'Unknown'),
                'patient_age': patient_data.get('patient_profile', {}).get('age'),
                'chief_complaint': chief_complaint,
                'confidence_score': report_data.get('confidence_score') if report_data else None,
                'confidence_tier': report_data.get('confidence_tier') if report_data else None,
                'created_at': consultation_data.get('created_at'),
                'interview_complete': consultation_data.get('interview_complete', False)
            })

        return result

    except Exception as e:
        print(f"Get doctor dashboard error: {e}")
        raise HTTPException(status_code=500, detail='Failed to get dashboard')


# ─────────────────────────────────────────────
#  CONSULTATION MANAGEMENT
# ─────────────────────────────────────────────

@router.post('/assign/{consultation_id}')
async def assign_consultation(
    consultation_id: str,
    user_id: str = Depends(require_doctor),
    db=Depends(get_firestore)
):
    try:
        consultation_ref = db.collection('consultations').document(consultation_id)
        consultation = consultation_ref.get()

        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data.get('doctor_id'):
            raise HTTPException(status_code=400, detail='Consultation already assigned')

        consultation_ref.update({
            'doctor_id': user_id,
            'status': 'approved',
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        return {'message': 'Consultation assigned successfully'}

    except Exception as e:
        print(f"Assign consultation error: {e}")
        raise HTTPException(status_code=500, detail='Failed to assign consultation')

@router.post('/reject/{consultation_id}')
async def reject_consultation(
    consultation_id: str,
    rejection_data: DoctorReject,
    user_id: str = Depends(require_doctor),
    db=Depends(get_firestore)
):
    try:
        consultation_ref = db.collection('consultations').document(consultation_id)
        consultation = consultation_ref.get()

        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data.get('doctor_id') and consultation_data['doctor_id'] != user_id:
            raise HTTPException(status_code=403, detail='Consultation assigned to another doctor')

        consultation_ref.update({
            'doctor_id': user_id,
            'status': 'rejected',
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        # Add rejection note to report if exists
        reports = db.collection('reports').where('consultation_id', '==', consultation_id).limit(1).get()
        if reports:
            report_ref = reports[0].reference
            report_ref.update({
                'doctor_notes': rejection_data.reason,
                'approved_at': firestore.SERVER_TIMESTAMP
            })

        return {'message': 'Consultation rejected'}

    except Exception as e:
        print(f"Reject consultation error: {e}")
        raise HTTPException(status_code=500, detail='Failed to reject consultation')

@router.post('/approve/{consultation_id}')
async def approve_consultation(
    consultation_id: str,
    approval_data: DoctorApproval,
    user_id: str = Depends(require_doctor),
    db=Depends(get_firestore)
):
    try:
        consultation_ref = db.collection('consultations').document(consultation_id)
        consultation = consultation_ref.get()

        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data.get('doctor_id') != user_id:
            raise HTTPException(status_code=403, detail='Consultation not assigned to you')

        # Update report with doctor notes and prescription
        reports = db.collection('reports').where('consultation_id', '==', consultation_id).limit(1).get()
        if reports:
            report_ref = reports[0].reference
            update_data = {
                'doctor_notes': approval_data.notes,
                'prescription': approval_data.prescription,
                'approved_at': firestore.SERVER_TIMESTAMP
            }
            report_ref.update(update_data)

        consultation_ref.update({
            'status': 'approved',
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        return {'message': 'Consultation approved with prescription'}

    except Exception as e:
        print(f"Approve consultation error: {e}")
        raise HTTPException(status_code=500, detail='Failed to approve consultation')


# ─────────────────────────────────────────────
#  DOCTOR CONSULTATIONS
# ─────────────────────────────────────────────

@router.get('/consultations')
async def get_doctor_consultations(user_id: str = Depends(require_doctor), db=Depends(get_firestore)):
    try:
        # Get consultations assigned to this doctor
        consultations = db.collection('consultations').where('doctor_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).get()

        result = []
        for consultation in consultations:
            consultation_data = consultation.to_dict()

            # Get patient info
            patient_doc = db.collection('users').document(consultation_data['patient_id']).get()
            patient_data = patient_doc.to_dict() if patient_doc.exists else {}

            # Get report if exists
            reports = db.collection('reports').where('consultation_id', '==', consultation.id).limit(1).get()
            report_data = None
            if reports:
                report_data = reports[0].to_dict()

            # Get chief complaint from structured data
            chief_complaint = 'Consultation'
            if report_data and report_data.get('structured_json'):
                try:
                    structured = json.loads(report_data['structured_json'])
                    chief_complaint = structured.get('chief_complaint', 'Consultation')
                except:
                    pass

            result.append({
                'consultation_id': consultation.id,
                'patient_name': patient_data.get('name', 'Unknown'),
                'patient_age': patient_data.get('patient_profile', {}).get('age'),
                'chief_complaint': chief_complaint,
                'status': consultation_data['status'],
                'confidence_score': report_data.get('confidence_score') if report_data else None,
                'confidence_tier': report_data.get('confidence_tier') if report_data else None,
                'created_at': consultation_data.get('created_at'),
                'approved_at': report_data.get('approved_at') if report_data else None,
                'doctor_notes': report_data.get('doctor_notes') if report_data else None,
                'prescription': report_data.get('prescription') if report_data else None
            })

        return result

    except Exception as e:
        print(f"Get doctor consultations error: {e}")
        raise HTTPException(status_code=500, detail='Failed to get consultations')

    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()

    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'created_at': user.created_at.isoformat(),
        'specialization': profile.specialization if profile else None,
        'qualification': profile.qualification if profile else None,
        'experience_years': profile.experience_years if profile else None,
        'license_number': profile.license_number if profile else None,
        'hospital': profile.hospital if profile else None,
        'department': profile.department if profile else None,
        'phone': profile.phone if profile else None,
        'consultation_hours': profile.consultation_hours if profile else None,
        'bio': profile.bio if profile else None,
        'languages': profile.languages if profile else None,
    }


@router.put('/profile')
async def update_doctor_profile(
    body: DoctorProfileUpdate,
    user_id: int = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()

    if not profile:
        profile = DoctorProfile(user_id=user_id)
        db.add(profile)

    for field, value in body.dict(exclude_none=True).items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    db.commit()

    return {'message': 'Profile updated successfully'}


# ─────────────────────────────────────────────
#  CONSULTATIONS
# ─────────────────────────────────────────────

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

    messages = db.query(Message).filter(
        Message.consultation_id == consultation_id
    ).order_by(Message.timestamp).all()

    # Patient background profile
    profile = db.query(PatientProfile).filter(
        PatientProfile.user_id == consultation.patient_id
    ).first()

    patient_profile = None
    if profile:
        patient_profile = {
            'age': profile.age,
            'gender': profile.gender,
            'blood_group': profile.blood_group,
            'height_cm': profile.height_cm,
            'weight_kg': profile.weight_kg,
            'chronic_conditions': profile.chronic_conditions,
            'past_surgeries': profile.past_surgeries,
            'current_medications': profile.current_medications,
            'known_allergies': profile.known_allergies,
            'family_history': profile.family_history,
            'smoking': profile.smoking,
            'alcohol': profile.alcohol,
            'exercise': profile.exercise,
            'emergency_contact_name': profile.emergency_contact_name,
            'emergency_contact_phone': profile.emergency_contact_phone,
        }

    return {
        'id': consultation.id,
        'patient_name': patient.name if patient else 'Unknown',
        'patient_email': patient.email if patient else 'Unknown',
        'patient_profile': patient_profile,
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