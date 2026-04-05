import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import PatientLogin from './pages/PatientLogin'
import PatientConsultation from './pages/PatientConsultation'
import DoctorLogin from './pages/DoctorLogin'
import DoctorDashboard from './pages/DoctorDashboard'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/patient-login" element={<PatientLogin />} />
                <Route path="/patient/consultation" element={<PatientConsultation />} />
                <Route path="/doctor-login" element={<DoctorLogin />} />
                <Route path="/doctor/dashboard" element={<DoctorDashboard />} />
                <Route path="*" element={<Navigate to="/" />} />
            </Routes>
        </BrowserRouter>
    )
}

export default App
