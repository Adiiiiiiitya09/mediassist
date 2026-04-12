import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: "AIzaSyB9Q9VRGuN15069NkzlUsodcZEVDOusF7k",
  authDomain: "intelehealth-172ad.firebaseapp.com",
  projectId: "intelehealth-172ad",
  storageBucket: "intelehealth-172ad.firebasestorage.app",
  messagingSenderId: "350290767061",
  appId: "1:350290767061:web:30038c4f610b747c03465c",
  measurementId: "G-MLK5J24F76"
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export default app
