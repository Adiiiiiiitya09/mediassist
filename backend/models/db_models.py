"""
Firestore Database Structure for MediAssist

Collections:
  1. users/
     - uid: Firebase UID (document ID)
     - name: string
     - email: string
     - role: 'patient' | 'doctor'
     - created_at: timestamp
     - updated_at: timestamp
     - patient_profile: object (if role='patient')
     - doctor_profile: object (if role='doctor')

  2. patient_profiles/
     - user_id: string (Firebase UID)
     - age: number
     - gender: string
     - blood_group: string
     - height_cm: float
     - weight_kg: float
     - chronic_conditions: string
     - past_surgeries: string
     - current_medications: string
     - known_allergies: string
     - family_history: string
     - smoking: string
     - alcohol: string
     - exercise: string
     - emergency_contact_name: string
     - emergency_contact_phone: string
     - updated_at: timestamp

  3. doctor_profiles/
     - user_id: string (Firebase UID)
     - specialization: string
     - qualification: string
     - experience_years: number
     - license_number: string
     - hospital: string
     - department: string
     - phone: string
     - consultation_hours: string
     - bio: string
     - languages: string
     - updated_at: timestamp

  4. consultations/
     - id: string (document ID)
     - patient_id: string (Firebase UID)
     - doctor_id: string (Firebase UID, nullable)
     - status: 'pending' | 'approved' | 'rejected'
     - interview_complete: boolean
     - created_at: timestamp
     - updated_at: timestamp

  5. messages/
     - id: string (document ID)
     - consultation_id: string
     - role: 'user' | 'assistant'
     - content: string
     - timestamp: timestamp

  6. reports/
     - id: string (document ID)
     - consultation_id: string
     - structured_json: string (JSON)
     - prediction_json: string (JSON)
     - confidence_score: float
     - confidence_tier: string
     - doctor_notes: string (nullable)
     - prescription: string (nullable)
     - approved_at: timestamp (nullable)
"""

import enum

class UserRole(str, enum.Enum):
    patient = 'patient'
    doctor = 'doctor'

class ConsultStatus(str, enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'

class DoctorProfile(Base):
    __tablename__ = 'doctor_profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    specialization = Column(String(100), nullable=True)
    qualification = Column(String(200), nullable=True)
    experience_years = Column(Integer, nullable=True)
    license_number = Column(String(50), nullable=True)
    hospital = Column(String(200), nullable=True)
    department = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    consultation_hours = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    languages = Column(String(200), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Consultation(Base):
    __tablename__ = 'consultations'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('users.id'))
    doctor_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(Enum(ConsultStatus), default=ConsultStatus.pending)
    interview_complete = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'))
    role = Column(String(20))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), unique=True)
    structured_json = Column(Text)
    prediction_json = Column(Text)
    confidence_score = Column(Float)
    confidence_tier = Column(String(10))
    doctor_notes = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)

    @staticmethod
    def from_dict(data: dict) -> 'PatientProfile':
        return PatientProfile(
            user_id=data.get('user_id'),
            age=data.get('age'),
            gender=data.get('gender'),
            blood_group=data.get('blood_group'),
            height_cm=data.get('height_cm'),
            weight_kg=data.get('weight_kg'),
            chronic_conditions=data.get('chronic_conditions'),
            past_surgeries=data.get('past_surgeries'),
            current_medications=data.get('current_medications'),
            known_allergies=data.get('known_allergies'),
            family_history=data.get('family_history'),
            smoking=data.get('smoking'),
            alcohol=data.get('alcohol'),
            exercise=data.get('exercise'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'age': self.age,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'chronic_conditions': self.chronic_conditions,
            'past_surgeries': self.past_surgeries,
            'current_medications': self.current_medications,
            'known_allergies': self.known_allergies,
            'family_history': self.family_history,
            'smoking': self.smoking,
            'alcohol': self.alcohol,
            'exercise': self.exercise,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'updated_at': self.updated_at
        }

class DoctorProfile:
    def __init__(self, user_id: str, specialization: Optional[str] = None,
                 qualification: Optional[str] = None, experience_years: Optional[int] = None,
                 license_number: Optional[str] = None, hospital: Optional[str] = None,
                 department: Optional[str] = None, phone: Optional[str] = None,
                 consultation_hours: Optional[str] = None, bio: Optional[str] = None,
                 languages: Optional[str] = None, updated_at: datetime = None):
        self.user_id = user_id
        self.specialization = specialization
        self.qualification = qualification
        self.experience_years = experience_years
        self.license_number = license_number
        self.hospital = hospital
        self.department = department
        self.phone = phone
        self.consultation_hours = consultation_hours
        self.bio = bio
        self.languages = languages
        self.updated_at = updated_at or datetime.utcnow()

    @staticmethod
    def from_dict(data: dict) -> 'DoctorProfile':
        return DoctorProfile(
            user_id=data.get('user_id'),
            specialization=data.get('specialization'),
            qualification=data.get('qualification'),
            experience_years=data.get('experience_years'),
            license_number=data.get('license_number'),
            hospital=data.get('hospital'),
            department=data.get('department'),
            phone=data.get('phone'),
            consultation_hours=data.get('consultation_hours'),
            bio=data.get('bio'),
            languages=data.get('languages'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'specialization': self.specialization,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'license_number': self.license_number,
            'hospital': self.hospital,
            'department': self.department,
            'phone': self.phone,
            'consultation_hours': self.consultation_hours,
            'bio': self.bio,
            'languages': self.languages,
            'updated_at': self.updated_at
        }

class Consultation:
    def __init__(self, id: str, patient_id: str, doctor_id: Optional[str] = None,
                 status: ConsultStatus = ConsultStatus.pending, interview_complete: int = 0,
                 created_at: datetime = None):
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.status = status
        self.interview_complete = interview_complete
        self.created_at = created_at or datetime.utcnow()

    @staticmethod
    def from_dict(data: dict, doc_id: str) -> 'Consultation':
        return Consultation(
            id=doc_id,
            patient_id=data.get('patient_id'),
            doctor_id=data.get('doctor_id'),
            status=ConsultStatus(data.get('status', 'pending')),
            interview_complete=data.get('interview_complete', 0),
            created_at=data.get('created_at')
        )

    def to_dict(self) -> dict:
        return {
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'status': self.status.value,
            'interview_complete': self.interview_complete,
            'created_at': self.created_at
        }

class Message:
    def __init__(self, id: str, consultation_id: str, role: str, content: str,
                 timestamp: datetime = None):
        self.id = id
        self.consultation_id = consultation_id
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()

    @staticmethod
    def from_dict(data: dict, doc_id: str) -> 'Message':
        return Message(
            id=doc_id,
            consultation_id=data.get('consultation_id'),
            role=data.get('role'),
            content=data.get('content'),
            timestamp=data.get('timestamp')
        )

    def to_dict(self) -> dict:
        return {
            'consultation_id': self.consultation_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }

class Report:
    def __init__(self, id: str, consultation_id: str, structured_json: str,
                 prediction_json: str, confidence_score: float, confidence_tier: str,
                 doctor_notes: Optional[str] = None, prescription: Optional[str] = None,
                 approved_at: Optional[datetime] = None):
        self.id = id
        self.consultation_id = consultation_id
        self.structured_json = structured_json
        self.prediction_json = prediction_json
        self.confidence_score = confidence_score
        self.confidence_tier = confidence_tier
        self.doctor_notes = doctor_notes
        self.prescription = prescription
        self.approved_at = approved_at

    @staticmethod
    def from_dict(data: dict, doc_id: str) -> 'Report':
        return Report(
            id=doc_id,
            consultation_id=data.get('consultation_id'),
            structured_json=data.get('structured_json'),
            prediction_json=data.get('prediction_json'),
            confidence_score=data.get('confidence_score'),
            confidence_tier=data.get('confidence_tier'),
            doctor_notes=data.get('doctor_notes'),
            prescription=data.get('prescription'),
            approved_at=data.get('approved_at')
        )

    def to_dict(self) -> dict:
        return {
            'consultation_id': self.consultation_id,
            'structured_json': self.structured_json,
            'prediction_json': self.prediction_json,
            'confidence_score': self.confidence_score,
            'confidence_tier': self.confidence_tier,
            'doctor_notes': self.doctor_notes,
            'prescription': self.prescription,
            'approved_at': self.approved_at
        }