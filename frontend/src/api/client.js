import axios from 'axios'
import { auth } from '../firebase'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
})

// Attach Firebase ID token to every request automatically
api.interceptors.request.use(async config => {
    let tokenSet = false
    if (auth.currentUser) {
        try {
            const idToken = await auth.currentUser.getIdToken()
            config.headers.Authorization = `Bearer ${idToken}`
            localStorage.setItem('token', idToken)
            tokenSet = true
        } catch (error) {
            console.error('Error getting Firebase ID token:', error)
        }
    }
    
    if (!tokenSet) {
        const token = localStorage.getItem('token')
        if (token) config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

export default api