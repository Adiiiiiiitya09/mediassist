from firebase_admin import auth as firebase_auth, firestore
from firebase_config import initialize_firebase, get_firestore_client
import os

# Initialize Firebase
initialize_firebase()
db = get_firestore_client()

def create_demo_users():
    try:
        # Demo Doctor
        doctor_user = firebase_auth.create_user(
            email='doctor@demo.com',
            password='demo123',
            display_name='Dr. Demo Doctor'
        )

        doctor_data = {
            'uid': doctor_user.uid,
            'name': 'Dr. Demo Doctor',
            'email': 'doctor@demo.com',
            'role': 'doctor',
            'created_at': firestore.SERVER_TIMESTAMP,
            'doctor_profile': {
                'specialization': 'General Medicine',
                'qualification': 'MD',
                'experience_years': 10,
                'license_number': 'DEMO12345',
                'hospital': 'Demo General Hospital',
                'department': 'Internal Medicine',
                'phone': '+1234567890',
                'consultation_hours': '9 AM - 5 PM',
                'bio': 'Experienced general physician with 10 years of practice.',
                'languages': 'English, Spanish'
            }
        }

        db.collection('users').document(doctor_user.uid).set(doctor_data)
        print(f'Demo doctor created with UID: {doctor_user.uid}')

        # Demo Patient
        patient_user = firebase_auth.create_user(
            email='patient@demo.com',
            password='demo123',
            display_name='Demo Patient'
        )

        patient_data = {
            'uid': patient_user.uid,
            'name': 'Demo Patient',
            'email': 'patient@demo.com',
            'role': 'patient',
            'created_at': firestore.SERVER_TIMESTAMP,
            'patient_profile': {
                'age': 30,
                'gender': 'male',
                'blood_group': 'O+',
                'height_cm': 175.0,
                'weight_kg': 70.0,
                'chronic_conditions': 'None',
                'past_surgeries': 'Appendectomy (2015)',
                'current_medications': 'None',
                'known_allergies': 'Penicillin',
                'family_history': 'Father - Hypertension',
                'smoking': 'never',
                'alcohol': 'occasional',
                'exercise': 'moderate',
                'emergency_contact_name': 'Jane Doe',
                'emergency_contact_phone': '+0987654321'
            }
        }

        db.collection('users').document(patient_user.uid).set(patient_data)
        print(f'Demo patient created with UID: {patient_user.uid}')

        print('Demo users created successfully!')

    except Exception as e:
        print(f'Error creating demo users: {e}')

if __name__ == '__main__':
    create_demo_users()