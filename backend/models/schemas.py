from pydantic import BaseModel
from typing import List, Optional

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

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
