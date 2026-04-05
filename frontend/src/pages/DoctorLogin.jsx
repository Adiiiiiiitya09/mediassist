import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function DoctorLogin() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [isRegister, setIsRegister] = useState(false)
    const [error, setError] = useState('')
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const endpoint = isRegister ? '/auth/register' : '/auth/login'
            const data = isRegister
                ? { email, password, name, role: 'doctor' }
                : { email, password }

            const response = await api.post(endpoint, data)
            localStorage.setItem('token', response.data.access_token)
            navigate('/doctor/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Error')
        }
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="bg-white border border-gray-200 rounded-lg p-8 max-w-md w-full">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
                    {isRegister ? 'Doctor Registration' : 'Doctor Login'}
                </h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {isRegister && (
                        <input
                            type="text"
                            placeholder="Full Name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                            required
                        />
                    )}

                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full border border-gray-300 rounded px-3 py-2"
                        required
                    />

                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full border border-gray-300 rounded px-3 py-2"
                        required
                    />

                    {error && <p className="text-red-600 text-sm">{error}</p>}

                    <button
                        type="submit"
                        className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 rounded"
                    >
                        {isRegister ? 'Register' : 'Login'}
                    </button>
                </form>

                <p className="text-center text-sm text-gray-600 mt-4">
                    {isRegister ? 'Already have an account?' : "Don't have an account?"}
                    <button
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
