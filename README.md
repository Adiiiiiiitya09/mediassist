# MediAssist - AI-Assisted Telehealth Consultation System

## Project Overview
A Human-in-the-Loop telehealth system where:
1. **Patient** submits symptoms via AI-led interview (Claude Sonnet 4)
2. **ML Model** suggests top-5 conditions (ExtraTreesClassifier - 100% accuracy)
3. **Licensed Doctor** reviews and approves/rejects with final diagnosis
4. **Patient** never sees disease suggestions - only doctor can approve

### Key Technologies
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **AI**: Claude Sonnet 4 (claude-sonnet-4-20250514) + ExtraTreesClassifier
- **ML**: scikit-learn, rapidfuzz, pandas
- **Auth**: JWT (python-jose) + bcrypt

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Anthropic API Key

### 1. Download Datasets
Download from Kaggle: [itachi9604/disease-symptom-description-dataset](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset)

Place these 4 CSV files in `backend/ml/`:
- `dataset.csv`
- `Symptom-severity.csv`
- `symptom_Description.csv`
- `symptom_precaution.csv`

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env and add your ANTHROPIC_API_KEY and SECRET_KEY

# Train ML model (run once)
python ml/train_model.py
# Output: Accuracy: 1.0000
# Generated: extratrees_model.pkl, label_encoder.pkl, symptom_list.json

# Start backend server
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Application: http://localhost:5173
```

## Project Structure

```
telehealth-ai/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables
│   ├── routes/
│   │   ├── auth.py             # Register, login, JWT
│   │   ├── consultation.py      # Patient interview endpoints
│   │   └── doctor.py           # Doctor dashboard endpoints
│   ├── services/
│   │   ├── ai_interview.py      # Claude API - interview logic
│   │   ├── scribe.py           # Claude API - JSON extraction
│   │   └── predictor.py        # ExtraTrees prediction
│   ├── models/
│   │   ├── db_models.py        # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic request/response schemas
│   └── ml/
│       ├── train_model.py      # Train ExtraTrees
│       ├── extratrees_model.pkl    # Saved model
│       ├── label_encoder.pkl    # Disease label encoder
│       ├── symptom_list.json    # 131 symptoms
│       └── [4 CSV dataset files]
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx
│   │   │   ├── PatientLogin.jsx
│   │   │   ├── PatientConsultation.jsx
│   │   │   ├── DoctorLogin.jsx
│   │   │   └── DoctorDashboard.jsx
│   │   ├── components/
│   │   │   ├── ChatBubble.jsx
│   │   │   ├── ConfidenceMeter.jsx
│   │   │   ├── DiseaseCard.jsx
│   │   │   └── ConsultationCard.jsx
│   │   ├── api/
│   │   │   └── client.js       # Axios instance with JWT
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── index.html
└── README.md
```

## API Endpoints

### Authentication
- **POST** `/auth/register` - Register user
- **POST** `/auth/login` - Login user

### Patient Consultation
- **POST** `/consultation/start` - Start new consultation
- **POST** `/consultation/message` - Send message, receive AI reply
- **GET** `/consultation/status/{id}` - Check consultation status

### Doctor Dashboard
- **GET** `/doctor/pending` - List pending consultations
- **GET** `/doctor/consultation/{id}` - Get full consultation details
- **POST** `/doctor/approve/{id}` - Approve with notes + prescription
- **POST** `/doctor/reject/{id}` - Reject with notes

## Ethical Constraints (Enforced in Code)

1. ✅ **Patient API NEVER returns disease names** - Only role='patient' tokens get {reply, is_complete}
2. ✅ **Doctor routes check role==doctor** - Return 403 for patient tokens
3. ✅ **Confidence score capped at 99%** - Never 100%, human doctor has final authority
4. ✅ **No disease suggestions to patients** - Patient sees only encouragement message
5. ✅ **AI system prompt forbids mentioning diseases** - "NEVER suggest or mention any disease"

## Testing the System

### As Patient
1. Register at **Patient Login**
2. Chat with AI assistant about your symptoms
3. System completes interview after 10-14 exchanges
4. Message shows "✅ Your information has been submitted..."

### As Doctor
1. Register at **Doctor Login**
2. View pending consultations in left panel
3. Click a consultation to see:
   - Patient summary (chief complaint, medications, allergies)
   - Vital flags (urgent details)
   - Top 5 AI-suggested conditions with probabilities
   - Full interview transcript
4. Add notes and prescription (optional)
5. Click **Approve** or **Reject**

## Model Details

### Dataset
- **Source**: Kaggle - Disease Symptom Dataset
- **Rows**: 4,920 (perfectly balanced)
- **Diseases**: 41 conditions
- **Samples per disease**: 120
- **Features**: 131 binary symptom columns
- **Test Accuracy**: 100% (clean, structured dataset - expected for academic use)

### ML Pipeline
1. **Feature Engineering**: Free-text symptoms → binary vector (131 dims)
2. **Fuzzy Matching**: rapidfuzz maps symptoms to master list (70% threshold)
3. **Prediction**: ExtraTreesClassifier → top-5 with probabilities
4. **Confidence Scoring**: `min(prob × coverage × quality_mult × 100, 99.0)`

### Confidence Tiers
- **High**: Score ≥ 80% (green)
- **Medium**: Score 50-79% (yellow)
- **Low**: Score < 50% (red)

## Configuration

### Backend `.env`
```
ANTHROPIC_API_KEY=sk-xxx
SECRET_KEY=your_long_random_secret_key_here
DATABASE_URL=sqlite:///./telehealth.db
```

### Frontend `.env`
```
VITE_API_URL=http://localhost:8000
```

## Development

### Frontend Build
```bash
npm run build  # Production build to dist/
npm run preview  # Preview production build
```

### Backend Testing
```bash
# Manually test endpoints at http://localhost:8000/docs
```

## Author
**Aditya Sharma** (23STUCHH011239)  
**Supervisor**: Dr. Nafis Uddin Khan  
**Institution**: IcfaiTech FST

## License
Academic Project - For educational purposes only
