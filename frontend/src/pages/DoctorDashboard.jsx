import React, { useState, useEffect } from 'react'
import ConsultationCard from '../components/ConsultationCard'
import ConfidenceMeter from '../components/ConfidenceMeter'
import DiseaseCard from '../components/DiseaseCard'
import api from '../api/client'

export default function DoctorDashboard() {
    const [consultations, setConsultations] = useState([])
    const [selectedConsult, setSelectedConsult] = useState(null)
    const [notes, setNotes] = useState('')
    const [prescription, setPrescription] = useState('')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchPending()
    }, [])

    const fetchPending = async () => {
        try {
            const response = await api.get('/doctor/pending')
            setConsultations(response.data)
            setLoading(false)
        } catch (err) {
            console.error(err)
            setLoading(false)
        }
    }

    const loadDetail = async (id) => {
        try {
            const response = await api.get(`/doctor/consultation/${id}`)
            setSelectedConsult(response.data)
            setNotes('')
            setPrescription('')
        } catch (err) {
            console.error(err)
        }
    }

    const handleApprove = async () => {
        try {
            await api.post(`/doctor/approve/${selectedConsult.id}`, { notes, prescription })
            setSelectedConsult(null)
            fetchPending()
        } catch (err) {
            console.error(err)
        }
    }

    const handleReject = async () => {
        try {
            await api.post(`/doctor/reject/${selectedConsult.id}`, { notes })
            setSelectedConsult(null)
            fetchPending()
        } catch (err) {
            console.error(err)
        }
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="bg-blue-700 text-white p-4">
                <h1 className="text-2xl font-bold">Doctor Dashboard</h1>
            </div>

            <div className="flex h-screen">
                {/* Left Panel - Consultation List */}
                <div className="w-80 border-r border-gray-200 bg-white p-4 overflow-y-auto">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Pending Consultations</h2>

                    {loading ? (
                        <p className="text-gray-500">Loading...</p>
                    ) : consultations.length === 0 ? (
                        <p className="text-gray-500">No pending consultations</p>
                    ) : (
                        consultations.map(c => (
                            <ConsultationCard
                                key={c.id}
                                id={c.id}
                                patientName={c.patient_name}
                                date={c.date}
                                urgency={c.urgency}
                                onSelect={() => loadDetail(c.id)}
                            />
                        ))
                    )}
                </div>

                {/* Right Panel - Consultation Detail */}
                <div className="flex-1 p-6 overflow-y-auto">
                    {selectedConsult ? (
                        <div className="max-w-4xl">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">{selectedConsult.patient_name}</h2>

                            {/* Confidence Meter */}
                            <ConfidenceMeter
                                score={selectedConsult.confidence_score}
                                tier={selectedConsult.confidence_tier}
                                color={selectedConsult.prediction?.color || 'gray'}
                            />

                            {/* Patient Summary */}
                            <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
                                <h3 className="font-semibold text-gray-900 mb-2">Patient Summary</h3>
                                <p><strong>Chief Complaint:</strong> {selectedConsult.structured_data?.chief_complaint}</p>
                                <p className="text-sm text-gray-600 mt-2">
                                    <strong>Medications:</strong> {selectedConsult.structured_data?.current_medications?.join(', ') || 'None'}
                                </p>
                                <p className="text-sm text-gray-600">
                                    <strong>Allergies:</strong> {selectedConsult.structured_data?.allergies?.join(', ') || 'None'}
                                </p>
                                {selectedConsult.structured_data?.vital_flags?.length > 0 && (
                                    <p className="text-sm text-red-600 mt-2">
                                        <strong>🚨 Vital Flags:</strong> {selectedConsult.structured_data.vital_flags.join(', ')}
                                    </p>
                                )}
                            </div>

                            {/* Top Conditions */}
                            {selectedConsult.prediction?.top5 && (
                                <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
                                    <h3 className="font-semibold text-gray-900 mb-3">Top Conditions (AI Suggestions – Doctor Only)</h3>
                                    {selectedConsult.prediction.top5.map((d, idx) => (
                                        <DiseaseCard
                                            key={idx}
                                            disease={d.disease}
                                            probability={d.probability}
                                            description={d.description}
                                            precautions={d.precautions}
                                        />
                                    ))}
                                </div>
                            )}

                            {/* Transcript */}
                            <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
                                <h3 className="font-semibold text-gray-900 mb-2">Interview Transcript</h3>
                                <div className="space-y-2 max-h-64 overflow-y-auto text-sm">
                                    {selectedConsult.transcript?.map((msg, idx) => (
                                        <p key={idx} className={msg.role === 'user' ? 'text-blue-700' : 'text-teal-700'}>
                                            <strong>{msg.role === 'user' ? 'Patient' : 'AI'}:</strong> {msg.content}
                                        </p>
                                    ))}
                                </div>
                            </div>

                            {/* Doctor Decision */}
                            <div className="bg-white border border-gray-200 rounded-lg p-4">
                                <h3 className="font-semibold text-gray-900 mb-3">Doctor Decision</h3>
                                <textarea
                                    placeholder="Doctor Notes..."
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2 mb-3"
                                    rows="3"
                                />
                                <textarea
                                    placeholder="Prescription..."
                                    value={prescription}
                                    onChange={(e) => setPrescription(e.target.value)}
                                    className="w-full border border-gray-300 rounded px-3 py-2 mb-4"
                                    rows="3"
                                />
                                <div className="flex gap-4">
                                    <button
                                        onClick={handleApprove}
                                        className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 rounded"
                                    >
                                        ✓ Approve
                                    </button>
                                    <button
                                        onClick={handleReject}
                                        className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 rounded"
                                    >
                                        ✕ Reject
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex items-center justify-center text-gray-500">
                            <p>Select a consultation to view details</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
