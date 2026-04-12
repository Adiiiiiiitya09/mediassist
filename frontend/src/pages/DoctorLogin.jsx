import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { auth } from '../firebase'
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, updateProfile } from 'firebase/auth'
import api from '../api/client'

export default function DoctorLogin() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [isRegister, setIsRegister] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const [specialization, setSpecialization] = useState('')
    const [qualification, setQualification] = useState('')
    const [experienceYears, setExperienceYears] = useState('')
    const [licenseNumber, setLicenseNumber] = useState('')
    const [hospital, setHospital] = useState('')
    const [department, setDepartment] = useState('')
    const [phone, setPhone] = useState('')
    const [consultationHours, setConsultationHours] = useState('')
    const [bio, setBio] = useState('')
    const [languages, setLanguages] = useState('')

    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            if (isRegister) {
                // Step 1 — Create user in Firebase Auth
                const userCredential = await createUserWithEmailAndPassword(auth, email, password)
                const firebaseUser = userCredential.user

                // Step 2 — Update display name
                await updateProfile(firebaseUser, { displayName: name })

                // Step 3 — Register in our SQLite backend with firebase_uid
                await api.post('/auth/register', {
                    firebase_uid: firebaseUser.uid,
                    name,
                    email,
                    role: 'doctor',
                    specialization: specialization || null,
                    qualification: qualification || null,
                    experience_years: experienceYears ? parseInt(experienceYears) : null,
                    license_number: licenseNumber || null,
                    hospital: hospital || null,
                    department: department || null,
                    phone: phone || null,
                    consultation_hours: consultationHours || null,
                    bio: bio || null,
                    languages: languages || null
                })

                navigate('/doctor/dashboard')

            } else {
                // Login — Firebase handles password verification
                await signInWithEmailAndPassword(auth, email, password)
                navigate('/doctor/dashboard')
            }

        } catch (err) {
            console.error('Auth error:', err)
            if (err.code === 'auth/email-already-in-use') {
                setError('Email already registered. Please login.')
            } else if (err.code === 'auth/weak-password') {
                setError('Password must be at least 6 characters.')
            } else if (err.code === 'auth/user-not-found' || err.code === 'auth/wrong-password' || err.code === 'auth/invalid-credential') {
                setError('Invalid email or password.')
            } else if (err.code === 'auth/invalid-email') {
                setError('Please enter a valid email address.')
            } else if (err.response?.data?.detail) {
                setError(err.response.data.detail)
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
                    {isRegister ? 'Doctor Registration' : 'Doctor Login'}
                </h2>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Basic Information</h3>

                        {isRegister && (
                            <input type="text" placeholder="Full Name" value={name}
                                onChange={e => setName(e.target.value)}
                                className="w-full border border-gray-300 rounded px-3 py-2" required />
                        )}

                        <input type="email" placeholder="Email" value={email}
                            onChange={e => setEmail(e.target.value)}
                            className="w-full border border-gray-300 rounded px-3 py-2" required />

                        <input type="password" placeholder="Password (min 6 characters)" value={password}
                            onChange={e => setPassword(e.target.value)}
                            className="w-full border border-gray-300 rounded px-3 py-2" required />
                    </div>

                    {isRegister && (
                        <>
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Professional Details <span className="text-sm font-normal text-gray-400">(optional)</span></h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <input type="text" placeholder="Specialization (e.g. Cardiology)" value={specialization}
                                        onChange={e => setSpecialization(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                    <input type="text" placeholder="Qualification (e.g. MD, MBBS)" value={qualification}
                                        onChange={e => setQualification(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                    <input type="number" placeholder="Years of Experience" value={experienceYears}
                                        onChange={e => setExperienceYears(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                    <input type="text" placeholder="License Number" value={licenseNumber}
                                        onChange={e => setLicenseNumber(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Hospital & Contact</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <input type="text" placeholder="Hospital / Clinic Name" value={hospital}
                                        onChange={e => setHospital(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                    <input type="text" placeholder="Department" value={department}
                                        onChange={e => setDepartment(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                    <input type="tel" placeholder="Phone Number" value={phone}
                                        onChange={e => setPhone(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                    <input type="text" placeholder="Consultation Hours (e.g. Mon-Fri 9AM-5PM)" value={consultationHours}
                                        onChange={e => setConsultationHours(e.target.value)}
                                        className="w-full border border-gray-300 rounded px-3 py-2" />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Additional Info</h3>
                                <textarea placeholder="Professional Bio" value={bio}
                                    onChange={e => setBio(e.target.value)} rows={3}
                                    className="w-full border border-gray-300 rounded px-3 py-2 resize-vertical" />
                                <input type="text" placeholder="Languages Spoken (e.g. English, Hindi)" value={languages}
                                    onChange={e => setLanguages(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2" />
                            </div>
                        </>
                    )}

                    {error && <p className="text-red-600 text-sm bg-red-50 p-3 rounded">{error}</p>}

                    <button type="submit" disabled={loading}
                        className="w-full bg-blue-700 hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2 rounded">
                        {loading ? 'Please wait...' : (isRegister ? 'Register' : 'Login')}
                    </button>
                </form>

                <p className="text-center text-sm text-gray-600 mt-4">
                    {isRegister ? 'Already have an account?' : "Don't have an account?"}
                    <button onClick={() => { setIsRegister(!isRegister); setError('') }}
                        className="text-blue-700 ml-2 font-semibold">
                        {isRegister ? 'Login' : 'Register'}
                    </button>
                </p>
            </div>
        </div>
    )
}
