import React, { useState, useEffect, useRef } from 'react'
import ChatBubble from '../components/ChatBubble'
import api from '../api/client'

export default function PatientConsultation() {
    const [consultationId, setConsultationId] = useState(null)
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [isComplete, setIsComplete] = useState(false)
    const messagesEndRef = useRef(null)

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search)
        const continueId = urlParams.get('continue')

        const startConsultation = async () => {
            try {
                if (continueId) {
                    // Load existing consultation for reconsult
                    setConsultationId(parseInt(continueId))
                    // Load existing messages
                    const historyResponse = await api.get(`/consultation/status/${continueId}`)
                    // For reconsult, we start fresh but could load previous context if needed
                    setMessages([{
                        role: 'assistant',
                        content: 'Welcome back! I see you\'re following up on a previous consultation. Let\'s update your symptoms and medical information. What changes have you noticed since your last visit?'
                    }])
                } else {
                    // Start new consultation
                    const response = await api.post('/consultation/start')
                    setConsultationId(response.data.consultation_id)
                    setMessages([{
                        role: 'assistant',
                        content: 'Hello! I\'m your medical intake assistant. I\'ll help gather information about your symptoms. Can you start by telling me what brings you in today?'
                    }])
                }
            } catch (err) {
                console.error(err)
            }
        }

        startConsultation()
    }, [])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = async (e) => {
        e.preventDefault()

        if (!input.trim() || !consultationId || loading || isComplete) return

        const userMessage = { role: 'user', content: input }
        setMessages([...messages, userMessage])
        setInput('')
        setLoading(true)

        try {
            const response = await api.post('/consultation/message', {
                consultation_id: consultationId,
                message: input
            })

            const aiMessage = { role: 'assistant', content: response.data.reply }
            setMessages(prev => [...prev, aiMessage])

            if (response.data.is_complete) {
                setIsComplete(true)
            }
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <div className="bg-blue-700 text-white p-4">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold">Patient Consultation</h1>
                    <button
                        onClick={() => window.location.href = '/dashboard'}
                        className="bg-white text-blue-700 px-4 py-2 rounded font-semibold hover:bg-gray-100"
                    >
                        ← Back to Dashboard
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-2xl mx-auto space-y-4">
                    {messages.map((msg, idx) => (
                        <ChatBubble key={idx} role={msg.role} content={msg.content} />
                    ))}

                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-teal-50 border border-teal-200 px-4 py-2 rounded-lg">
                                <div className="flex gap-1">
                                    <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce"></div>
                                    <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                </div>
                            </div>
                        </div>
                    )}

                    {isComplete && (
                        <div className="bg-green-50 border border-green-200 rounded p-4 text-green-800">
                            <p>✅ Your information has been submitted. A doctor will review your case shortly.</p>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {!isComplete && (
                <div className="border-t border-gray-200 bg-white p-6">
                    <form onSubmit={handleSend} className="max-w-2xl mx-auto flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                            placeholder="Type your response..."
                            className="flex-1 border border-gray-300 rounded px-4 py-2 disabled:bg-gray-100"
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="bg-blue-700 hover:bg-blue-800 text-white font-semibold px-6 py-2 rounded disabled:opacity-50"
                        >
                            Send
                        </button>
                    </form>
                </div>
            )}
        </div>
    )
}
