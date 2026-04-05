# Step-by-Step Setup Guide

## ⚙️ Prerequisites
Ensure you have installed:
- Python 3.8 or higher
- Node.js 16 or higher
- Git (optional)
- Anthropic API Key (from https://console.anthropic.com)

Verify installations:
```bash
python --version
node --version
npm --version
```

---

## 📥 STEP 1: Download Dataset (Important!)

The ML model requires 4 CSV files from Kaggle:

1. Go to: https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset
2. Click "Download" and login with your Kaggle account
3. Extract the downloaded ZIP

Required files:
- `dataset.csv` (Main disease-symptom mapping)
- `Symptom-severity.csv` (Symptom severity levels)
- `symptom_Description.csv` (Disease descriptions)
- `symptom_precaution.csv` (Precautions for each disease)

Copy these 4 files to:
```
backend/ml/
```

Your folder should look like:
```
backend/ml/
├── dataset.csv
├── Symptom-severity.csv
├── symptom_Description.csv
├── symptom_precaution.csv
└── train_model.py
```

---

## 🔑 STEP 2: Configure Backend

### 2.1 Open backend/.env
```
backend/.env
```

### 2.2 Add your API Key
Edit the file and add:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=this_is_a_secret_key_make_it_long_and_random_12345
DATABASE_URL=sqlite:///./telehealth.db
```

Replace `sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` with your actual Anthropic API key from:
https://console.anthropic.com/account/keys

---

## 🤖 STEP 3: Train ML Model

This is a one-time setup!

```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Train the ML model (takes 2-5 minutes)
python ml/train_model.py
```

**Expected output:**
```
Accuracy: 1.0000
Saved: extratrees_model.pkl  label_encoder.pkl  symptom_list.json
```

**Files created:**
- `extratrees_model.pkl` (Trained decision tree model)
- `label_encoder.pkl` (Maps disease names to IDs)
- `symptom_list.json` (All 131 symptoms)

⚠️ If you see errors:
- Make sure all 4 CSV files are in `backend/ml/`
- Check Python version is 3.8+
- Try: `pip install --upgrade scikit-learn pandas numpy`

---

## 🚀 STEP 4: Start Backend Server

```bash
# Make sure you're in backend directory
cd backend

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
Uvicorn running on http://127.0.0.1:8000
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

✅ Leave this terminal running!

---

## 📦 STEP 5: Setup Frontend

Open a **NEW terminal** (don't close the backend one)

```bash
# Navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

✅ Leave this terminal running!

---

## 🎯 STEP 6: Test the Application

Open your browser and go to: **http://localhost:5173/**

### 6.1 Test Patient Flow
1. Click "I am a Patient"
2. Click "Register" (default tab)
3. Fill in:
   - Name: `Test Patient`
   - Email: `patient@test.com`
   - Password: `password123`
4. Click Register
5. Start chatting about your symptoms
   - Try: "I have a fever and headache"
   - Keep chatting for 10-14 exchanges
   - System will auto-complete and show "✅ Your information has been submitted..."

### 6.2 Test Doctor Flow
1. Go back to http://localhost:5173/
2. Click "I am a Doctor"
3. Click "Register"
4. Fill in:
   - Name: `Dr. Smith`
   - Email: `doctor@test.com`
   - Password: `password123`
5. Click Register
6. You'll see the pending consultation from the patient
7. Click on it to see:
   - Patient summary
   - AI confidence score
   - Top 5 disease suggestions (doctor only!)
   - Full interview transcript
8. Add some notes and click "Approve" or "Reject"

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] 4 CSV files in `backend/ml/`
- [ ] ANTHROPIC_API_KEY added to `backend/.env`
- [ ] ML model trained successfully (100% accuracy)
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Can register as patient
- [ ] Can chat with AI
- [ ] Can register as doctor
- [ ] Doctor can see pending consultations
- [ ] Doctor sees AI confidence score with disclaimer

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'anthropic'"
**Solution:**
```bash
pip install anthropic
```

### Issue: "No such file 'dataset.csv'"
**Solution:**
- Download from Kaggle: https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset
- Extract and place 4 CSV files in `backend/ml/`

### Issue: "ANTHROPIC_API_KEY not set"
**Solution:**
- Edit `backend/.env`
- Add: `ANTHROPIC_API_KEY=sk-ant-xxxxx...`
- Get key from: https://console.anthropic.com/account/keys

### Issue: "Address already in use" for port 8000 or 5173
**Solution:**
- Port 8000: Try `uvicorn main:app --reload --port 8001`
- Port 5173: Update frontend API URL in `frontend/.env`: `VITE_API_URL=http://localhost:8001`

### Issue: Frontend shows blank page
**Solution:**
- Check browser console (F12) for errors
- Make sure backend is running on http://localhost:8000
- Clear browser cache (Ctrl+Shift+Delete)

### Issue: "Cannot POST /consultation/message"
**Solution:**
- Backend not running
- Start with: `cd backend && uvicorn main:app --reload --port 8000`

---

## 📊 System Architecture

```
USER BROWSER (http://localhost:5173)
        ↓
    React App
    ├─ Patient Pages
    │  └─ Chat with AI
    └─ Doctor Pages
       └─ Review & Approve
        ↓ (HTTP + JWT)
    FastAPI Server (http://localhost:8000)
    ├─ /auth/* (Register, Login)
    ├─ /consultation/* (Chat, Status)
    └─ /doctor/* (Pending, Approve, Reject)
        ↓
    Services
    ├─ ai_interview.py (Claude API)
    ├─ scribe.py (Claude API)
    └─ predictor.py (ML Model)
        ↓
    Database (SQLite)
    ├─ users
    ├─ consultations
    ├─ messages
    └─ reports
```

---

## 🚀 Next Steps

1. **Explore the code**:
   - Backend: `backend/routes/` - API endpoints
   - Frontend: `frontend/src/pages/` - User interfaces
   - ML: `backend/ml/predictor.py` - Disease prediction

2. **Customize**:
   - Change colors in CSS files
   - Modify AI interview prompt in `ai_interview.py`
   - Add more diseases by retraining on larger dataset

3. **Deploy**:
   - Backend: Use gunicorn for production
   - Frontend: Build with `npm run build`, deploy to Vercel/Netlify
   - Database: Migrate to PostgreSQL for production

---

## 📞 Support

For issues:
1. Check the troubleshooting section above
2. Verify all steps completed
3. Check that both backend and frontend are running
4. Review the README.md for more details

---

## 🎓 Project Details

- **Student**: Aditya Sharma (23STUCHH011239)
- **Supervisor**: Dr. Nafis Uddin Khan
- **Institution**: IcfaiTech FST
- **Model**: Claude Sonnet 4 (claude-sonnet-4-20250514)
- **ML Algorithm**: ExtraTreesClassifier
- **Database**: SQLite
- **Architecture**: Human-in-the-Loop

Good luck! 🚀
