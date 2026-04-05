export default function ChatBubble({ role, content }) {
    const isAI = role === 'assistant'

    return (
        <div className={`flex ${isAI ? 'justify-start' : 'justify-end'} mb-4`}>
            <div className={`max-w-sm px-4 py-2 rounded-lg ${isAI
                    ? 'bg-teal-50 border border-teal-200 text-gray-800'
                    : 'bg-blue-700 text-white'
                }`}>
                {isAI && <p className="text-xs font-semibold text-teal-700 mb-1">AI Assistant</p>}
                <p>{content}</p>
            </div>
        </div>
    )
}
