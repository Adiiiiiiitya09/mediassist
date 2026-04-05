import React from 'react'
import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
    const navigate = useNavigate()

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">MediAssist</h1>
                <p className="text-lg text-gray-600">AI-Assisted Telehealth Consultation System</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-2xl">
                <div className="bg-white border border-gray-200 rounded-lg p-8 text-center hover:shadow-lg transition">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">I am a Patient</h2>
                    <p className="text-gray-600 mb-6">Start your consultation with our AI assistant</p>
                    <button
                        onClick={() => navigate('/patient-login')}
                        className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 rounded"
                    >
                        Patient Login
                    </button>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-8 text-center hover:shadow-lg transition">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">I am a Doctor</h2>
                    <p className="text-gray-600 mb-6">Review and approve consultations</p>
                    <button
                        onClick={() => navigate('/doctor-login')}
                        className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 rounded"
                    >
                        Doctor Login
                    </button>
                </div>
            </div>

            <footer className="absolute bottom-4 text-center text-sm text-gray-500">
                <p>IcfaiTech FST • Project by Aditya Sharma (23STUCHH011239)</p>
            </footer>
        </div>
    )
}
