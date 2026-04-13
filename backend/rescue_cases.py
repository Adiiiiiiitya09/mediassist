import json
from database import SessionLocal
from models.db_models import Consultation, Message, Report
from services.scribe import extract_structured_data
from services.predictor import predict

db = SessionLocal()
stuck_consults = db.query(Consultation).filter(Consultation.interview_complete == 0).all()
count = 0
for c in stuck_consults:
    messages = db.query(Message).filter(Message.consultation_id == c.id).order_by(Message.timestamp).all()
    if any('[INTERVIEW COMPLETE]' in m.content for m in messages):
        print(f"Rescuing consultation {c.id}...")
        history = [{'role': m.role, 'content': m.content} for m in messages]
        structured = extract_structured_data(history)
        symptoms = [s['name'] for s in structured.get('symptoms', [])]
        symptoms += structured.get('associated_symptoms', [])
        prediction = predict(symptoms, structured.get('interview_quality', 'medium'))
        
        db.add(Report(
            consultation_id=c.id,
            structured_json=json.dumps(structured),
            prediction_json=json.dumps(prediction),
            confidence_score=prediction['score'],
            confidence_tier=prediction['tier'],
        ))
        c.interview_complete = 1
        db.commit()
        count += 1
        print(f"Rescued consultation {c.id}")

db.close()
if count == 0:
    print("No stuck cases found.")
