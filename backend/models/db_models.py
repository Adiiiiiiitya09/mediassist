from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    patient = 'patient'
    doctor = 'doctor'

class ConsultStatus(str, enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(150), unique=True)
    password_hash = Column(String(255))
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), unique=True)
    structured_json = Column(Text)  # Scribe output
    prediction_json = Column(Text)  # ExtraTrees top-5 (NEVER sent to patient)
    confidence_score = Column(Float)
    confidence_tier = Column(String(10))
    doctor_notes = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
