export default function DiseaseCard({ disease, probability, description, precautions }) {
    const [expanded, setExpanded] = React.useState(false)

    return (
        <div className="bg-white border border-gray-200 rounded-lg p-3 mb-2">
            <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
                <div>
                    <p className="font-semibold text-gray-800">{disease}</p>
                    <p className="text-sm text-gray-600">{probability}%</p>
                </div>
                <span className="text-lg">{expanded ? '▼' : '▶'}</span>
            </div>

            {expanded && (
                <div className="mt-3 text-sm text-gray-700 space-y-2">
                    {description && <p><strong>Description:</strong> {description}</p>}
                    {precautions && precautions.length > 0 && (
                        <div>
                            <strong>Precautions:</strong>
                            <ul className="list-disc list-inside">
                                {precautions.map((p, i) => <li key={i}>{p}</li>)}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

import React from 'react'
