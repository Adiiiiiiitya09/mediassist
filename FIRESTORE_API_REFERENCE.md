# Firestore API Reference & Code Examples

Quick reference for using the MediAssist API after Firestore migration.

---

## Authentication Endpoints

### 1. Register User

**Endpoint**: `POST /auth/register`

**Frontend Code**:
```javascript
// Create user in Firebase Auth first
const userCredential = await createUserWithEmailAndPassword(auth, email, password);
const firebaseUser = userCredential.user;
const idToken = await firebaseUser.getIdToken();

// Send to backend with profile data
const response = await api.post('/auth/register', {
  firebase_uid: firebaseUser.uid,
  name: "John Doe",
  email: email,
  role: "patient",  // or "doctor"
  
  // Patient-specific fields
  age: 35,
  gender: "Male",
  blood_group: "O+",
  height_cm: 180,
  weight_kg: 75,
  chronic_conditions: "Diabetes",
  past_surgeries: "None",
  current_medications: "Metformin",
  known_allergies: "Penicillin",
  family_history: "Hypertension",
  smoking: "No",
  alcohol: "Occasionally",
  exercise: "3x per week",
  emergency_contact_name: "Jane Doe",
  emergency_contact_phone: "+1234567890"
});
```

**Backend**: Already configured in `routes/auth.py`  
**Firestore Result**:
```firestore
db.collection('users').document('abc123').set({
  uid: 'abc123',
  name: 'John Doe',
  email: 'john@example.com',
  role: 'patient',
  created_at: <timestamp>,
  updated_at: <timestamp>,
  patient_profile: { age: 35, ... }
})
```

---

### 2. Login User

**Endpoint**: `POST /auth/login`

**Frontend Code**:
```javascript
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();

const response = await api.post('/auth/login', {
  firebase_token: idToken
});

// Response: { uid, role, name }
// Redirect based on role:
if (response.role === 'patient') {
  window.location.href = '/patient/consultation';
} else if (response.role === 'doctor') {
  window.location.href = '/doctor/dashboard';
}
```

---

### 3. Verify Token (Check Auth State)

**Endpoint**: `GET /auth/verify`  
**Required Header**: `Authorization: Bearer {id_token}`

**Frontend Code** (Axios interceptor handles this):
```javascript
// On app load, check if user is logged in
const response = await api.get('/auth/verify');
// Returns: { uid, role, email, name, patient_profile/doctor_profile }
```

---

## Patient Endpoints

### 1. Get Patient Profile

**Endpoint**: `GET /patient/profile`

**Frontend Code**:
```javascript
const profile = await api.get('/patient/profile');
// Returns: { name, email, role, created_at, age, gender, blood_group, ... }

// Display profile
console.log(`Patient: ${profile.name}, Age: ${profile.age}, Blood: ${profile.blood_group}`);
```

**Backend** (in `routes/patient.py`):
```python
@router.get('/profile')
async def get_profile(user_id: str = Depends(require_patient)):
    user_doc = db.collection('users').document(user_id).get()
    user_data = user_doc.to_dict()
    profile = user_data.get('patient_profile', {})
    profile.update({
        'name': user_data.get('name'),
        'email': user_data.get('email'),
        'created_at': user_data.get('created_at')
    })
    return profile
```

---

### 2. Update Patient Profile

**Endpoint**: `PUT /patient/profile`

**Frontend Code**:
```javascript
const updated = await api.put('/patient/profile', {
  age: 36,  // Updated age
  weight_kg: 78,  // Updated weight
  current_medications: "Metformin 500mg",
  // Only send fields you want to update (null fields are ignored)
});
```

**Backend**: Updates only `patient_profile` nested document in Firestore

---

## Consultation Endpoints

### 1. Start Consultation

**Endpoint**: `POST /consultation/start`

**Frontend Code**:
```javascript
const result = await api.post('/consultation/start');
// Returns: { consultation_id: "cons_xyz789" }

// Save consultation_id for this session
sessionStorage.setItem('consultation_id', result.consultation_id);
```

**Firestore Effect**:
```firestore
db.collection('consultations').document('cons_xyz789').set({
  id: 'cons_xyz789',
  patient_id: 'abc123',  // Current user's Firebase UID
  status: 'pending',
  interview_complete: false,
  created_at: <timestamp>,
  updated_at: <timestamp>
})
```

---

### 2. Send Message (Chat)

**Endpoint**: `POST /consultation/message`

**Frontend Code**:
```javascript
const consultation_id = sessionStorage.getItem('consultation_id');

const result = await api.post('/consultation/message', {
  consultation_id: consultation_id,
  message: "I've had a headache for 3 days"
});
// Returns: { reply: "...", is_complete: false }

// Add reply to chat UI
addMessageToChat('assistant', result.reply);

// If is_complete = true, interview is done and report was generated
if (result.is_complete) {
  showMessage('Interview complete. A doctor will review your case shortly.');
}
```

**Firestore Effect**:
```firestore
// Patient message saved
db.collection('messages').document('msg_001').set({
  id: 'msg_001',
  consultation_id: 'cons_xyz789',
  role: 'user',
  content: 'I have had a headache for 3 days',
  timestamp: <timestamp>
})

// AI response saved
db.collection('messages').document('msg_002').set({
  id: 'msg_002',
  consultation_id: 'cons_xyz789',
  role: 'assistant',
  content: 'For how long have you had the headache?',
  timestamp: <timestamp>
})

// When interview complete (is_complete=true), report is created:
db.collection('reports').document('rep_001').set({
  id: 'rep_001',
  consultation_id: 'cons_xyz789',
  structured_json: '{"chief_complaint": "headache", ...}',
  prediction_json: '{"diseases": ["migraine", ...], "confidence": 85.5}',
  confidence_score: 85.5,
  confidence_tier: 'High',
  created_at: <timestamp>
})

// Consultation status updated
db.collection('consultations').document('cons_xyz789').update({
  interview_complete: true,
  updated_at: <timestamp>
})
```

---

### 3. Check Consultation Status

**Endpoint**: `GET /consultation/status/{consultation_id}`

**Frontend Code**:
```javascript
const status = await api.get(`/consultation/status/${consultation_id}`);
// Returns: { id, status, interview_complete }

if (status.interview_complete) {
  showMessage('Interview complete! A doctor will review.');
} else {
  showMessage('Waiting for doctor review...');
}
```

---

### 4. Get Consultation History

**Endpoint**: `GET /consultation/history`

**Frontend Code**:
```javascript
const history = await api.get('/consultation/history');
// Returns array of past consultations:
// [
//   {
//     consultation_id: "cons_xyz789",
//     status: "approved",
//     chief_complaint: "Headache",
//     confidence_score: 85.5,
//     confidence_tier: "High",
//     created_at: "2024-01-15T10:30:00Z"
//   },
//   ...
// ]

history.forEach(consult => {
  console.log(`${consult.chief_complaint} - ${consult.confidence_tier} confidence`);
});
```

---

## Doctor Endpoints

### 1. Get Doctor Profile

**Endpoint**: `GET /doctor/profile`

**Firestore Query** (backend):
```firestore
db.collection('users').document(doctor_uid).get()
→ Returns: doctor_profile nested in user document
```

---

### 2. Update Doctor Profile

**Endpoint**: `PUT /doctor/profile`

**Frontend Code**:
```javascript
const updated = await api.put('/doctor/profile', {
  specialization: "Cardiology",
  experience_years: 12,
  phone: "+1-555-0123",
  consultation_hours: "Mon-Fri 9AM-6PM, Sat 10AM-2PM",
  bio: "Dr. Jane Smith specializes in preventive cardiology..."
});
```

---

### 3. Get Doctor Dashboard

**Endpoint**: `GET /doctor/dashboard`

**Firestore Queries** (backend):
```firestore
// Get all pending consultations
db.collection('consultations')
  .where('status', '==', 'pending')
  .where('doctor_id', '==', None)
  .get()

// For each consultation:
// - Get patient info from users collection
// - Get report (if exists) from reports collection
```

**Response**:
```json
[
  {
    "consultation_id": "cons_001",
    "patient_name": "John Doe",
    "patient_info": {...},
    "chief_complaint": "Severe headache",
    "interview_complete": true,
    "confidence_tier": "High",
    "prediction": ["migraine", "tension headache", ...]
  },
  ...
]
```

---

### 4. Approve/Reject Consultation

**Endpoint**: `POST /doctor/approve` or `POST /doctor/reject`

**Frontend Code**:
```javascript
// Approve consultation
await api.post(`/doctor/approve/${consultation_id}`, {
  notes: "Follow up in 2 weeks if headaches persist",
  prescription: "Aspirin 500mg twice daily"
});

// Firestore effect:
// db.collection('consultations').document(consultation_id).update({
//   status: 'approved',
//   doctor_id: doctor_uid
// })
// db.collection('reports').document(report_id).update({
//   doctor_notes: "...",
//   prescription: "...",
//   approved_at: <timestamp>
// })
```

---

## Error Handling

### Common Errors

**No Token**:
```javascript
// Error: 401 Unauthorized "No token provided"
// Fix: Ensure Authorization header is set
// (Axios interceptor should handle this automatically)
```

**Invalid Token**:
```javascript
// Error: 401 Unauthorized "Invalid or expired token"
// Fix: User needs to log in again
window.location.href = '/login';
```

**User Not Found**:
```javascript
// Error: 404 "User not found"
// Fix: For registration - user already registered
// Fix: For other endpoints - database inconsistency
```

**Forbidden**:
```javascript
// Error: 403 "Forbidden"
// Fix: Patient trying to access doctor endpoint (or vice versa)
// Check role in auth token
```

---

## Performance Tips

### 1. Cache User Data
```javascript
// Don't call /auth/verify on every page load
const cachedUser = localStorage.getItem('user');
if (!cachedUser) {
  const user = await api.get('/auth/verify');
  localStorage.setItem('user', JSON.stringify(user));
}
```

### 2. Batch Message Loading
```javascript
// For consultation history, load top 10, then paginate
const history = await api.get('/consultation/history?limit=10&offset=0');
```

### 3. Real-time Updates (Future)
```javascript
// Firestore listeners (not yet implemented)
db.collection('consultations')
  .where('patient_id', '==', user_uid)
  .onSnapshot(snapshot => {
    console.log('Consultations updated:', snapshot.docs);
  });
```

---

## Frontend API Client Setup

Already configured in `frontend/src/api/client.js`:

```javascript
import axios from 'axios';
import { getAuth } from 'firebase/auth';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

// Interceptor: Add Firebase token to all requests
api.interceptors.request.use(async (config) => {
  const auth = getAuth();
  if (auth.currentUser) {
    const idToken = await auth.currentUser.getIdToken();
    config.headers.Authorization = `Bearer ${idToken}`;
  }
  return config;
});

export default api;
```

---

## Testing the API

### Using cURL

**Register**:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_uid": "abc123",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "patient",
    "age": 35,
    ...
  }'
```

**Login**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "'$ID_TOKEN'"}'
```

**Verify**:
```bash
curl http://localhost:8000/auth/verify \
  -H "Authorization: Bearer $ID_TOKEN"
```

### Using FastAPI Docs

1. Start backend: `python main.py`
2. Open: http://localhost:8000/docs
3. Click "Authorize" button
4. Paste Firebase ID token
5. Try endpoints interactively

---

## Security Checklist

- ✅ Never expose Firebase service account key (added to `.gitignore`)
- ✅ All endpoints require valid Firebase token
- ✅ Backend verifies token with Firebase Admin SDK
- ✅ User can only access their own data
- ✅ Role-based access control enforced (patient vs doctor)
- ✅ Firestore security rules restrict access
- ✅ Environment variables for sensitive config

---

**Happy Coding! 🚀**
