export default function ConfidenceMeter({ score, tier, color }) {
    const displayScore = Math.min(score, 99)
    const percentage = displayScore / 99 * 100

    const colorClass = color === 'green' ? 'bg-green-500' : color === 'yellow' ? 'bg-yellow-400' : 'bg-red-500'

    return (
        <div className="border border-gray-200 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">AI Data Quality Score</h3>
            <div className="flex items-center gap-4">
                <div className="flex-1">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className={`h-2 rounded-full ${colorClass}`} style={{ width: `${percentage}%` }}></div>
                    </div>
                </div>
                <span className="text-lg font-bold text-gray-800">{displayScore}%</span>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${tier === 'High' ? 'bg-green-100 text-green-800' :
                        tier === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                    }`}>{tier}</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">⚠️ This is a data quality indicator, not a diagnostic certainty score.</p>
        </div>
    )
}
