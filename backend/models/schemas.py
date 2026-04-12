from pydantic import BaseModel
from typing import Optional

class PatientRegister(BaseModel):
    firebase_uid: str
    name: str
    email: str
    password: str = 'firebase'
    role: str
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    chronic_conditions: Optional[str] = None
    past_surgeries: Optional[str] = None
    current_medications: Optional[str] = None
    known_allergies: Optional[str] = None
    family_history: Optional[str] = None
    smoking: Optional[str] = None
    alcohol: Optional[str] = None
    exercise: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    firebase_token: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class ConsultationStart(BaseModel):
    pass

class MessageRequest(BaseModel):
    consultation_id: int
    message: str

class MessageResponse(BaseModel):
    reply: str
    is_complete: bool

class ConsultationStatus(BaseModel):
    id: int
    status: str
    interview_complete: int

class DoctorApproval(BaseModel):
    notes: str
    prescription: str

class DoctorReject(BaseModel):
    notes: str

class PatientProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    chronic_conditions: Optional[str] = None
    past_surgeries: Optional[str] = None
    current_medications: Optional[str] = None
    known_allergies: Optional[str] = None
    family_history: Optional[str] = None
    smoking: Optional[str] = None
    alcohol: Optional[str] = None
    exercise: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class DoctorProfileUpdate(BaseModel):
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    license_number: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    consultation_hours: Optional[str] = None
    bio: Optional[str] = None
    languages: Optional[str] = None