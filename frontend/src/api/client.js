import axios from 'axios'
import { auth } from '../firebase'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
})

// Attach Firebase ID token to every request automatically
api.interceptors.request.use(async config => {
    if (auth.currentUser) {
        try {
            const idToken = await auth.currentUser.getIdToken()
            config.headers.Authorization = `Bearer ${idToken}`
        } catch (error) {
            console.error('Error getting Firebase ID token:', error)
        }
    }
    return config
})

export default api