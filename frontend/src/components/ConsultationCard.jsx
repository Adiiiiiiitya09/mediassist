import React from 'react'

export default function ConsultationCard({ id, patientName, date, urgency, onSelect }) {
    const urgencyColor = urgency === 'High' ? 'bg-red-500' : urgency === 'Medium' ? 'bg-yellow-400' : 'bg-green-500'

    return (
        <div
            className="bg-white border border-gray-200 rounded-lg p-4 mb-2 cursor-pointer hover:shadow-md transition"
            onClick={onSelect}
        >
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <p className="font-semibold text-gray-800">{patientName}</p>
                    <p className="text-xs text-gray-500">{new Date(date).toLocaleDateString()}</p>
                </div>
                <div className={`w-4 h-4 rounded-full ${urgencyColor}`}></div>
            </div>
        </div>
    )
}
