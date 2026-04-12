import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { auth } from '../firebase'
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    updateProfile,
    GoogleAuthProvider,
    signInWithPopup,
    deleteUser
} from 'firebase/auth'
import api from '../api/client'

export default function PatientLogin() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [isRegister, setIsRegister] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    // Medical profile fields
    const [age, setAge] = useState('')
    const [gender, setGender] = useState('')
    const [bloodGroup, setBloodGroup] = useState('')
    const [height, setHeight] = useState('')
    const [weight, setWeight] = useState('')
    const [chronicConditions, setChronicConditions] = useState('')
    const [pastSurgeries, setPastSurgeries] = useState('')
    const [currentMedications, setCurrentMedications] = useState('')
    const [knownAllergies, setKnownAllergies] = useState('')
    const [familyHistory, setFamilyHistory] = useState('')
    const [smoking, setSmoking] = useState('')
    const [alcohol, setAlcohol] = useState('')
    const [exercise, setExercise] = useState('')
    const [emergencyContactName, setEmergencyContactName] = useState('')
    const [emergencyContactPhone, setEmergencyContactPhone] = useState('')

    const navigate = useNavigate()

    const handleGoogleSignIn = async (event) => {
        event.preventDefault()
        setError('')
        setLoading(true)

        try {
            const provider = new GoogleAuthProvider()
            const result = await signInWithPopup(auth, provider)
            const firebaseUser = result.user
            const idToken = await firebaseUser.getIdToken()

            // Store token in localStorage for dashboard access
            localStorage.setItem('token', idToken)

            // Try to register in backend (ignore if user already exists)
            try {
                await api.post('/auth/register', {
                    firebase_uid: firebaseUser.uid,
                    name: firebaseUser.displayName || 'Google User',
                    email: firebaseUser.email,
                    role: 'patient'
                })
            } catch (backendErr) {
                if (backendErr.response?.status !== 409) {
                    await deleteUser(firebaseUser)
                    throw new Error(backendErr.response?.data?.detail || 'Registration failed. Please try again.')
                }
            }

            navigate('/dashboard')
        } catch (err) {
            console.error('Google auth error:', err)
            if (err.code === 'auth/popup-closed-by-user') {
                setError('Google sign-in was cancelled.')
            } else if (err.code === 'auth/popup-blocked') {
                setError('Popup was blocked by browser. Please allow popups for this site.')
            } else if (err.code === 'auth/account-exists-with-different-credential') {
                setError('This email is already registered with another sign-in method.')
            } else if (err.message) {
                setError(err.message)
            } else {
                setError('Google sign-in failed. Please try again.')
            }
        } finally {
            setLoading(false)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        // Validate required fields
        if (isRegister && !name.trim()) {
            setError('Please enter your name')
            setLoading(false)
            return
        }
        if (!email.trim()) {
            setError('Please enter your email')
            setLoading(false)
            return
        }
        if (!password) {
            setError('Please enter your password')
            setLoading(false)
            return
        }

        try {
            if (isRegister) {
                // Step 1 — Create user in Firebase Auth
                const userCredential = await createUserWithEmailAndPassword(auth, email, password)
                const firebaseUser = userCredential.user
                const idToken = await firebaseUser.getIdToken()

                // Store token in localStorage for dashboard access
                localStorage.setItem('token', idToken)

                // Step 2 — Update display name in Firebase
                await updateProfile(firebaseUser, { displayName: name })

                // Step 3 — Register user profile in backend database (SQLAlchemy/SQLite)
                // If this fails, we DELETE the Firebase user so they can try again cleanly
                try {
                    await api.post('/auth/register', {
                        firebase_uid: firebaseUser.uid,
                        name,
                        email,
                        role: 'patient',
                        age: age ? parseInt(age) : null,
                        gender: gender || null,
                        blood_group: bloodGroup || null,
                        height_cm: height ? parseFloat(height) : null,
                        weight_kg: weight ? parseFloat(weight) : null,
                        chronic_conditions: chronicConditions || null,
                        past_surgeries: pastSurgeries || null,
                        current_medications: currentMedications || null,
                        known_allergies: knownAllergies || null,
                        family_history: familyHistory || null,
                        smoking: smoking || null,
                        alcohol: alcohol || null,
                        exercise: exercise || null,
                        emergency_contact_name: emergencyContactName || null,
                        emergency_contact_phone: emergencyContactPhone || null
                    })
                } catch (backendErr) {
                    // ⚠️ KEY FIX: Delete Firebase user so they can register again without
                    // getting "email already in use" on the next attempt
                    await deleteUser(firebaseUser)

                    const detail = backendErr.response?.data?.detail
                    throw new Error(detail || 'Backend registration failed. Please try again.')
                }

                navigate('/dashboard')

            } else {
                // Login — Firebase handles password verification
                const userCredential = await signInWithEmailAndPassword(auth, email, password)
                const idToken = await userCredential.user.getIdToken()

                // Store token in localStorage for dashboard access
                localStorage.setItem('token', idToken)

                // Verify backend user exists and token is valid
                await api.post('/auth/login', { firebase_token: idToken })
                navigate('/dashboard')
            }

        } catch (err) {
            console.error('Auth error:', err)
            if (err.code === 'auth/email-already-in-use') {
                setError('Email already registered. Please login instead.')
            } else if (err.code === 'auth/weak-password') {
                setError('Password must be at least 6 characters.')
            } else if (
                err.code === 'auth/user-not-found' ||
                err.code === 'auth/wrong-password' ||
                err.code === 'auth/invalid-credential'
            ) {
                setError('Invalid email or password.')
            } else if (err.code === 'auth/invalid-email') {
                setError('Please enter a valid email address.')
            } else if (err.message) {
                setError(err.message)
            } else {
                setError('An error occurred. Please try again.')
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-8">
            <div className="mb-6 flex items-center justify-center gap-3">
                <span className="text-3xl">🏥</span>
                <a href="/" className="text-3xl font-bold text-gray-900 no-underline hover:text-blue-700 transition">MediAssist</a>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
                    {isRegister ? 'Patient Registration' : 'Patient Login'}
                </h2>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Basic Information */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Basic Information</h3>

                        {isRegister && (
                            <input
                                type="text"
                                placeholder="Full Name *"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full border border-gray-300 rounded px-3 py-2"
                                required
                            />
                        )}

                        <input
                            type="email"
                            placeholder="Email *"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                            required
                        />

                        <input
                            type="password"
                            placeholder="Password *"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                            required
                        />
                    </div>

                    {/* Extended fields only shown during registration */}
                    {isRegister && (
                        <>
                            {/* Physical Details */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Physical Details</h3>

                                <div className="grid grid-cols-3 gap-4">
                                    <input
                                        type="number"
                                        placeholder="Age"
                                        value={age}
                                        onChange={(e) => setAge(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    />
                                    <select
                                        value={gender}
                                        onChange={(e) => setGender(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    >
                                        <option value="">Gender</option>
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                    <select
                                        value={bloodGroup}
                                        onChange={(e) => setBloodGroup(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    >
                                        <option value="">Blood Group</option>
                                        {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => (
                                            <option key={bg} value={bg}>{bg}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <input
                                        type="number"
                                        placeholder="Height (cm)"
                                        value={height}
                                        onChange={(e) => setHeight(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    />
                                    <input
                                        type="number"
                                        placeholder="Weight (kg)"
                                        value={weight}
                                        onChange={(e) => setWeight(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    />
                                </div>
                            </div>

                            {/* Medical History */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Medical History</h3>

                                <textarea
                                    placeholder="Chronic Conditions (e.g., Diabetes, Hypertension)"
                                    value={chronicConditions}
                                    onChange={(e) => setChronicConditions(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2 h-20 resize-none"
                                    rows={3}
                                />
                                <textarea
                                    placeholder="Past Surgeries (e.g., Appendectomy 2018)"
                                    value={pastSurgeries}
                                    onChange={(e) => setPastSurgeries(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2 h-20 resize-none"
                                    rows={3}
                                />
                                <textarea
                                    placeholder="Current Medications (e.g., Metformin 500mg)"
                                    value={currentMedications}
                                    onChange={(e) => setCurrentMedications(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2 h-20 resize-none"
                                    rows={3}
                                />
                                <input
                                    type="text"
                                    placeholder="Known Allergies (e.g., Penicillin, Dust)"
                                    value={knownAllergies}
                                    onChange={(e) => setKnownAllergies(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2"
                                />
                                <textarea
                                    placeholder="Family History (e.g., Father - Heart disease)"
                                    value={familyHistory}
                                    onChange={(e) => setFamilyHistory(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2 h-20 resize-none"
                                    rows={3}
                                />
                            </div>

                            {/* Lifestyle */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Lifestyle</h3>

                                <div className="grid grid-cols-3 gap-4">
                                    <select
                                        value={smoking}
                                        onChange={(e) => setSmoking(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    >
                                        <option value="">Smoking</option>
                                        <option value="never">Never</option>
                                        <option value="former">Former</option>
                                        <option value="current">Current</option>
                                    </select>
                                    <select
                                        value={alcohol}
                                        onChange={(e) => setAlcohol(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    >
                                        <option value="">Alcohol</option>
                                        <option value="never">Never</option>
                                        <option value="occasional">Occasional</option>
                                        <option value="regular">Regular</option>
                                    </select>
                                    <select
                                        value={exercise}
                                        onChange={(e) => setExercise(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    >
                                        <option value="">Exercise</option>
                                        <option value="sedentary">Sedentary</option>
                                        <option value="moderate">Moderate</option>
                                        <option value="active">Active</option>
                                    </select>
                                </div>
                            </div>

                            {/* Emergency Contact */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Emergency Contact</h3>

                                <div className="grid grid-cols-2 gap-4">
                                    <input
                                        type="text"
                                        placeholder="Emergency Contact Name"
                                        value={emergencyContactName}
                                        onChange={(e) => setEmergencyContactName(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    />
                                    <input
                                        type="tel"
                                        placeholder="Emergency Contact Phone"
                                        value={emergencyContactPhone}
                                        onChange={(e) => setEmergencyContactPhone(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2"
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {error && <p className="text-red-600 text-sm">{error}</p>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-700 hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded"
                    >
                        {loading ? 'Please wait...' : (isRegister ? 'Register' : 'Login')}
                    </button>

                    <div className="mt-4 text-center">
                        <p className="text-sm text-gray-500 mb-3">Or continue with</p>
                        <button
                            type="button"
                            onClick={handleGoogleSignIn}
                            disabled={loading}
                            className="w-full inline-flex items-center justify-center gap-2 border border-gray-300 rounded py-3 text-gray-700 hover:bg-gray-100"
                        >
                            <span>Continue with Google</span>
                        </button>
                    </div>
                </form>

                <p className="text-center text-sm text-gray-600 mt-6">
                    {isRegister ? 'Already have an account?' : "Don't have an account?"}
                    <button
                        type="button"
                        onClick={() => { setIsRegister(!isRegister); setError('') }}
                        className="text-blue-700 ml-2 font-semibold"
                    >
                        {isRegister ? 'Login' : 'Register'}
                    </button>
                </p>
            </div>
        </div>
    )
}