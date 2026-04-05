from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.db_models import User, UserRole, Base
from routes.auth import hash_password
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./telehealth.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Demo Doctor
doctor = User(
    name='Dr. Demo Doctor',
    email='doctor@demo.com',
    password_hash=hash_password('demo123'),
    role=UserRole.doctor
)
db.add(doctor)

# Demo Patient
patient = User(
    name='Demo Patient',
    email='patient@demo.com',
    password_hash=hash_password('demo123'),
    role=UserRole.patient
)
db.add(patient)

db.commit()
db.close()

print('Demo users created!')