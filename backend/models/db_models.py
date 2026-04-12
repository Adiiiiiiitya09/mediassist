from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    patient = 'patient'
    doctor  = 'doctor'

class ConsultStatus(str, enum.Enum):
    pending  = 'pending'
    approved = 'approved'
    rejected = 'rejected'

# ── Tables ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = 'users'

    id            = Column(Integer, primary_key=True, index=True)
    firebase_uid  = Column(String(128), unique=True, nullable=False)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, nullable=False)
    role          = Column(Enum(UserRole), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class PatientProfile(Base):
    __tablename__ = 'patient_profiles'

    id                      = Column(Integer, primary_key=True, index=True)
    user_id                 = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    age                     = Column(Integer, nullable=True)
    gender                  = Column(String(20), nullable=True)
    blood_group             = Column(String(10), nullable=True)
    height_cm               = Column(Float, nullable=True)
    weight_kg               = Column(Float, nullable=True)
    chronic_conditions      = Column(Text, nullable=True)
    past_surgeries          = Column(Text, nullable=True)
    current_medications     = Column(Text, nullable=True)
    known_allergies         = Column(String(300), nullable=True)
    family_history          = Column(Text, nullable=True)
    smoking                 = Column(String(20), nullable=True)
    alcohol                 = Column(String(20), nullable=True)
    exercise                = Column(String(20), nullable=True)
    emergency_contact_name  = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    updated_at              = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DoctorProfile(Base):
    __tablename__ = 'doctor_profiles'

    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    specialization     = Column(String(100), nullable=True)
    qualification      = Column(String(200), nullable=True)
    experience_years   = Column(Integer, nullable=True)
    license_number     = Column(String(50), nullable=True)
    hospital           = Column(String(200), nullable=True)
    department         = Column(String(100), nullable=True)
    phone              = Column(String(20), nullable=True)
    consultation_hours = Column(String(100), nullable=True)
    bio                = Column(Text, nullable=True)
    languages          = Column(String(200), nullable=True)
    updated_at         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Consultation(Base):
    __tablename__ = 'consultations'

    id                 = Column(Integer, primary_key=True, index=True)
    patient_id         = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_id          = Column(Integer, ForeignKey('users.id'), nullable=True)
    status             = Column(Enum(ConsultStatus), default=ConsultStatus.pending)
    interview_complete = Column(Integer, default=0)   # 0 = in progress, 1 = done
    created_at         = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = 'messages'

    id              = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)
    role            = Column(String(20), nullable=False)   # 'user' or 'assistant'
    content         = Column(Text, nullable=False)
    timestamp       = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = 'reports'

    id               = Column(Integer, primary_key=True, index=True)
    consultation_id  = Column(Integer, ForeignKey('consultations.id'), unique=True, nullable=False)
    structured_json  = Column(Text, nullable=True)    # Claude Scribe output
    prediction_json  = Column(Text, nullable=True)    # ExtraTrees top-5 (NEVER sent to patient)
    confidence_score = Column(Float, nullable=True)
    confidence_tier  = Column(String(10), nullable=True)
    doctor_notes     = Column(Text, nullable=True)
    prescription     = Column(Text, nullable=True)
    approved_at      = Column(DateTime, nullable=True)