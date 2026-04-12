from fastapi import APIRouter, Depends, HTTPException, Header
from firebase_admin import firestore
import os
import json
from typing import Optional
from datetime import datetime
from models.schemas import ConsultationStart, MessageRequest, MessageResponse, ConsultationStatus
from services.ai_interview import get_ai_response
from services.scribe import extract_structured_data
from services.predictor import predict
from firebase_config import get_firestore_client
from routes.auth import verify_firebase_token

router = APIRouter()

def get_firestore():
    return get_firestore_client()

def require_patient(decoded_token: dict = Depends(verify_firebase_token)):
    if decoded_token.get('role') != 'patient':
        raise HTTPException(status_code=403, detail='Forbidden')
    return decoded_token['uid']

def require_doctor(decoded_token: dict = Depends(verify_firebase_token)):
    if decoded_token.get('role') != 'doctor':
        raise HTTPException(status_code=403, detail='Forbidden')
    return decoded_token['uid']

# ─────────────────────────────────────────────
#  START / CHAT
# ─────────────────────────────────────────────

@router.post('/start')
async def start_consultation(user_id: str = Depends(require_patient), db=Depends(get_firestore)):
    try:
        # Create new consultation document
        consultation_ref = db.collection('consultations').document()
        consultation_data = {
            'id': consultation_ref.id,
            'patient_id': user_id,
            'status': 'pending',
            'interview_complete': False,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }

        consultation_ref.set(consultation_data)

        return {'consultation_id': consultation_ref.id}

    except Exception as e:
        print(f"Start consultation error: {e}")
        raise HTTPException(status_code=500, detail='Failed to start consultation')

@router.post('/message', response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    try:
        # Verify consultation belongs to user
        consultation_ref = db.collection('consultations').document(body.consultation_id)
        consultation = consultation_ref.get()

        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data['patient_id'] != user_id:
            raise HTTPException(status_code=403, detail='Forbidden')

        # Save patient message
        message_ref = db.collection('messages').document()
        message_data = {
            'id': message_ref.id,
            'consultation_id': body.consultation_id,
            'role': 'user',
            'content': body.message,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        message_ref.set(message_data)

        # Load full history
        messages = db.collection('messages').where('consultation_id', '==', body.consultation_id).order_by('timestamp').get()
        history = [{'role': msg.to_dict()['role'], 'content': msg.to_dict()['content']} for msg in messages]

        # Get AI reply
        reply, is_complete = get_ai_response(history)

        # Save AI reply
        ai_message_ref = db.collection('messages').document()
        ai_message_data = {
            'id': ai_message_ref.id,
            'consultation_id': body.consultation_id,
            'role': 'assistant',
            'content': reply,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        ai_message_ref.set(ai_message_data)

        # If done: run scribe + predictor, save Report
        if is_complete:
            structured = extract_structured_data(history)
            symptoms = [s['name'] for s in structured.get('symptoms', [])]
            symptoms += structured.get('associated_symptoms', [])

            prediction = predict(symptoms, structured.get('interview_quality', 'medium'))

            # Save report
            report_ref = db.collection('reports').document()
            report_data = {
                'id': report_ref.id,
                'consultation_id': body.consultation_id,
                'structured_json': json.dumps(structured),
                'prediction_json': json.dumps(prediction),
                'confidence_score': prediction['score'],
                'confidence_tier': prediction['tier'],
                'created_at': firestore.SERVER_TIMESTAMP
            }
            report_ref.set(report_data)

            # Update consultation status
            consultation_ref.update({
                'interview_complete': True,
                'updated_at': firestore.SERVER_TIMESTAMP
            })

        return {'reply': reply, 'is_complete': is_complete}

    except Exception as e:
        print(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail='Failed to send message')

# ─────────────────────────────────────────────
#  PATIENT — STATUS & HISTORY
# ─────────────────────────────────────────────

@router.get('/status/{consultation_id}', response_model=ConsultationStatus)
async def check_status(
    consultation_id: str,
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    try:
        consultation = db.collection('consultations').document(consultation_id).get()

        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data['patient_id'] != user_id:
            raise HTTPException(status_code=403, detail='Forbidden')

        return {
            'id': consultation_id,
            'status': consultation_data['status'],
            'interview_complete': consultation_data.get('interview_complete', False)
        }

    except Exception as e:
        print(f"Check status error: {e}")
        raise HTTPException(status_code=500, detail='Failed to check status')

@router.get('/history')
async def get_patient_history(
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    try:
        # Get all consultations for this patient
        consultations = db.collection('consultations').where('patient_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).get()

        result = []
        for consultation in consultations:
            consultation_data = consultation.to_dict()

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
                'status': consultation_data['status'],
                'interview_complete': consultation_data.get('interview_complete', False),
                'created_at': consultation_data['created_at'].isoformat() if consultation_data.get('created_at') else None,
                'chief_complaint': chief_complaint,
                'confidence_score': report_data.get('confidence_score') if report_data else None,
                'confidence_tier': report_data.get('confidence_tier') if report_data else None,
                'has_doctor_response': False  # TODO: Implement doctor responses
            })

        return result

    except Exception as e:
        print(f"Get history error: {e}")
        raise HTTPException(status_code=500, detail='Failed to get history')

@router.get('/report/{consultation_id}')
async def get_patient_report(
    consultation_id: str,
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    try:
        # Verify consultation ownership
        consultation = db.collection('consultations').document(consultation_id).get()
        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data['patient_id'] != user_id:
            raise HTTPException(status_code=403, detail='Forbidden')

        if not consultation_data.get('interview_complete', False):
            raise HTTPException(status_code=400, detail='Interview not complete yet')

        # Get report
        reports = db.collection('reports').where('consultation_id', '==', consultation_id).limit(1).get()
        if not reports:
            raise HTTPException(status_code=404, detail='Report not ready yet')

        report_data = reports[0].to_dict()
        structured = json.loads(report_data['structured_json'])

        # Get chat transcript
        messages = db.collection('messages').where('consultation_id', '==', consultation_id).order_by('timestamp').get()
        transcript = []
        for msg in messages:
            msg_data = msg.to_dict()
            transcript.append({
                'role': msg_data['role'],
                'content': msg_data['content'],
                'timestamp': msg_data['timestamp'].isoformat() if msg_data.get('timestamp') else None
            })

        response = {
            'consultation_id': consultation_id,
            'status': consultation_data['status'],
            'created_at': consultation_data['created_at'].isoformat() if consultation_data.get('created_at') else None,
            'confidence_score': report_data['confidence_score'],
            'confidence_tier': report_data['confidence_tier'],
            'chief_complaint': structured.get('chief_complaint', ''),
            'symptoms': structured.get('symptoms', []),
            'associated_symptoms': structured.get('associated_symptoms', []),
            'vital_flags': structured.get('vital_flags', []),
            'medical_history': structured.get('medical_history', []),
            'current_medications': structured.get('current_medications', []),
            'allergies': structured.get('allergies', []),
            'transcript': transcript,
            'doctor_notes': None,  # TODO: Implement doctor notes
            'prescription': None,  # TODO: Implement prescriptions
            'approved_at': None   # TODO: Implement approval timestamps
        }

        return response

    except Exception as e:
        print(f"Get report error: {e}")
        raise HTTPException(status_code=500, detail='Failed to get report')

# ─────────────────────────────────────────────
#  PATIENT — ACTIONS
# ─────────────────────────────────────────────

@router.delete('/{consultation_id}')
async def delete_consultation(
    consultation_id: str,
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    try:
        # Verify consultation ownership
        consultation = db.collection('consultations').document(consultation_id).get()
        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data['patient_id'] != user_id:
            raise HTTPException(status_code=403, detail='Forbidden')

        # Delete associated messages and reports
        # Note: Firestore doesn't support transactions across collections easily
        # In production, consider using Cloud Functions for cleanup

        # Delete messages
        messages = db.collection('messages').where('consultation_id', '==', consultation_id).get()
        for msg in messages:
            msg.reference.delete()

        # Delete reports
        reports = db.collection('reports').where('consultation_id', '==', consultation_id).get()
        for report in reports:
            report.reference.delete()

        # Delete consultation
        db.collection('consultations').document(consultation_id).delete()

        return {'message': 'Consultation deleted successfully'}

    except Exception as e:
        print(f"Delete consultation error: {e}")
        raise HTTPException(status_code=500, detail='Failed to delete consultation')

@router.post('/reconsult/{consultation_id}')
async def reconsult(
    consultation_id: str,
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    try:
        # Get the original consultation
        original = db.collection('consultations').document(consultation_id).get()
        if not original.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        original_data = original.to_dict()
        if original_data['patient_id'] != user_id:
            raise HTTPException(status_code=403, detail='Forbidden')

        if not original_data.get('interview_complete', False):
            raise HTTPException(status_code=400, detail='Cannot reconsult an incomplete consultation')

        # Create new consultation
        new_consultation_ref = db.collection('consultations').document()
        new_consultation_data = {
            'id': new_consultation_ref.id,
            'patient_id': user_id,
            'status': 'pending',
            'interview_complete': False,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        new_consultation_ref.set(new_consultation_data)

        # Add welcome message for reconsultation
        welcome_message_ref = db.collection('messages').document()
        welcome_message_data = {
            'id': welcome_message_ref.id,
            'consultation_id': new_consultation_ref.id,
            'role': 'assistant',
            'content': 'Welcome back! I see you\'re following up on a previous consultation. Let\'s update your symptoms and medical information. What changes have you noticed since your last visit?',
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        welcome_message_ref.set(welcome_message_data)

        return {'consultation_id': new_consultation_ref.id, 'message': 'Reconsultation started'}

    except Exception as e:
        print(f"Reconsult error: {e}")
        raise HTTPException(status_code=500, detail='Failed to start reconsultation')

@router.get('/download-report/{consultation_id}')
async def download_report(
    consultation_id: str,
    user_id: str = Depends(require_patient),
    db=Depends(get_firestore)
):
    try:
        # Verify consultation ownership
        consultation = db.collection('consultations').document(consultation_id).get()
        if not consultation.exists:
            raise HTTPException(status_code=404, detail='Consultation not found')

        consultation_data = consultation.to_dict()
        if consultation_data['patient_id'] != user_id:
            raise HTTPException(status_code=403, detail='Forbidden')

        if not consultation_data.get('interview_complete', False):
            raise HTTPException(status_code=400, detail='Report not available yet')

        # Get report
        reports = db.collection('reports').where('consultation_id', '==', consultation_id).limit(1).get()
        if not reports:
            raise HTTPException(status_code=404, detail='Report not found')

        report_data = reports[0].to_dict()
        structured = json.loads(report_data['structured_json'])

        # Format the report as text
        report_text = f"""
MEDICAL CONSULTATION REPORT
===========================

Consultation ID: {consultation_id}
Date: {consultation_data.get('created_at').strftime('%B %d, %Y') if consultation_data.get('created_at') else 'N/A'}
Status: {consultation_data['status'].title()}

PATIENT INFORMATION
-------------------
Chief Complaint: {structured.get('chief_complaint', 'Not specified')}

SYMPTOMS
--------
"""
        for symptom in structured.get('symptoms', []):
            report_text += f"• {symptom['name']}: Severity {symptom.get('severity', 'N/A')}/10"
            if symptom.get('duration'):
                report_text += f", Duration: {symptom['duration']}"
            report_text += "\n"

        if structured.get('associated_symptoms'):
            report_text += "\nAssociated Symptoms:\n"
            for symptom in structured['associated_symptoms']:
                report_text += f"• {symptom}\n"

        report_text += f"""

MEDICAL HISTORY
---------------
"""
        for history in structured.get('medical_history', []):
            report_text += f"• {history}\n"

        if structured.get('current_medications'):
            report_text += "\nCurrent Medications:\n"
            for med in structured['current_medications']:
                report_text += f"• {med}\n"

        if structured.get('allergies'):
            report_text += "\nKnown Allergies:\n"
            for allergy in structured['allergies']:
                report_text += f"• {allergy}\n"

        report_text += f"""

VITAL SIGNS & FLAGS
-------------------
"""
        if structured.get('vital_flags'):
            for flag in structured['vital_flags']:
                report_text += f"⚠ {flag}\n"
        else:
            report_text += "No vital flags detected\n"

        report_text += f"""

AI ANALYSIS
-----------
Confidence Score: {report_data['confidence_score']}%
Confidence Tier: {report_data['confidence_tier']}

DOCTOR REVIEW
-------------
"""
        # TODO: Add doctor review information when implemented
        report_text += "Awaiting doctor review\n"

        return {
            'filename': f'consultation_report_{consultation_id}.txt',
            'content': report_text,
            'consultation_id': consultation_id
        }

    except Exception as e:
        print(f"Download report error: {e}")
        raise HTTPException(status_code=500, detail='Failed to generate report')


# ─────────────────────────────────────────────
#  PATIENT — ACTIONS
# ─────────────────────────────────────────────

@router.delete('/{consultation_id}')
async def delete_consultation(
    consultation_id: int,
    user_id: int = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """
    Delete a consultation and all associated data (messages, reports)
    """
    consultation = db.query(Consultation).get(consultation_id)
    if not consultation or consultation.patient_id != user_id:
        raise HTTPException(status_code=404, detail='Consultation not found')

    # Delete associated messages and reports
    db.query(Message).filter(Message.consultation_id == consultation_id).delete()
    db.query(Report).filter(Report.consultation_id == consultation_id).delete()
    db.delete(consultation)
    db.commit()

    return {'message': 'Consultation deleted successfully'}


@router.post('/reconsult/{consultation_id}')
async def reconsult(
    consultation_id: int,
    user_id: int = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """
    Start a new consultation based on an existing one.
    Copies the structured data to help restart the interview.
    """
    # Get the original consultation
    original = db.query(Consultation).get(consultation_id)
    if not original or original.patient_id != user_id:
        raise HTTPException(status_code=404, detail='Consultation not found')

    if not original.interview_complete:
        raise HTTPException(status_code=400, detail='Cannot reconsult an incomplete consultation')

    # Create new consultation
    new_consultation = Consultation(patient_id=user_id, status=ConsultStatus.pending)
    db.add(new_consultation)
    db.commit()
    db.refresh(new_consultation)

    # Copy the structured data from the original report to help restart
    original_report = db.query(Report).filter(Report.consultation_id == consultation_id).first()
    if original_report:
        try:
            structured_data = json.loads(original_report.structured_json)
            # Add a system message to indicate this is a reconsultation
            welcome_message = Message(
                consultation_id=new_consultation.id,
                role='assistant',
                content=f'I see you\'re following up on a previous consultation. I\'ll help you update your symptoms and medical information. What changes have you noticed since your last visit?'
            )
            db.add(welcome_message)
            db.commit()
        except Exception:
            pass

    return {'consultation_id': new_consultation.id, 'message': 'Reconsultation started'}


@router.get('/download-report/{consultation_id}')
async def download_report(
    consultation_id: int,
    user_id: int = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """
    Generate and return a formatted report for download
    """
    consultation = db.query(Consultation).get(consultation_id)
    if not consultation or consultation.patient_id != user_id:
        raise HTTPException(status_code=404, detail='Consultation not found')

    if not consultation.interview_complete:
        raise HTTPException(status_code=400, detail='Report not available yet')

    report = db.query(Report).filter(Report.consultation_id == consultation_id).first()
    if not report:
        raise HTTPException(status_code=404, detail='Report not found')

    structured = json.loads(report.structured_json)

    # Format the report as text
    report_text = f"""
MEDICAL CONSULTATION REPORT
===========================

Consultation ID: {consultation_id}
Date: {consultation.created_at.strftime('%B %d, %Y')}
Status: {consultation.status.value.title()}

PATIENT INFORMATION
-------------------
Chief Complaint: {structured.get('chief_complaint', 'Not specified')}

SYMPTOMS
--------
"""
    for symptom in structured.get('symptoms', []):
        report_text += f"• {symptom['name']}: Severity {symptom.get('severity', 'N/A')}/10"
        if symptom.get('duration'):
            report_text += f", Duration: {symptom['duration']}"
        report_text += "\n"

    if structured.get('associated_symptoms'):
        report_text += "\nAssociated Symptoms:\n"
        for symptom in structured['associated_symptoms']:
            report_text += f"• {symptom}\n"

    report_text += f"""

MEDICAL HISTORY
---------------
"""
    for history in structured.get('medical_history', []):
        report_text += f"• {history}\n"

    if structured.get('current_medications'):
        report_text += "\nCurrent Medications:\n"
        for med in structured['current_medications']:
            report_text += f"• {med}\n"

    if structured.get('allergies'):
        report_text += "\nKnown Allergies:\n"
        for allergy in structured['allergies']:
            report_text += f"• {allergy}\n"

    report_text += f"""

VITAL SIGNS & FLAGS
-------------------
"""
    if structured.get('vital_flags'):
        for flag in structured['vital_flags']:
            report_text += f"⚠ {flag}\n"
    else:
        report_text += "No vital flags detected\n"

    report_text += f"""

AI ANALYSIS
-----------
Confidence Score: {report.confidence_score}%
Confidence Tier: {report.confidence_tier}

DOCTOR REVIEW
-------------
"""
    if consultation.status == ConsultStatus.approved and report.doctor_notes:
        report_text += f"Status: Approved\n"
        report_text += f"Doctor Notes:\n{report.doctor_notes}\n\n"
        if report.prescription:
            report_text += f"Prescription:\n{report.prescription}\n"
    else:
        report_text += "Awaiting doctor review\n"

    return {
        'filename': f'consultation_report_{consultation_id}.txt',
        'content': report_text,
        'consultation_id': consultation_id
    }