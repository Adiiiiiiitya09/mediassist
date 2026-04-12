import firebase_admin
from firebase_admin import credentials, auth, firestore
import os

# Path to your service account JSON file
# Place the downloaded JSON in backend/ folder
SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(__file__),
    'intelehealth-172ad-firebase-adminsdk-fbsvc-79eeb9e695.json'
)

def initialize_firebase():
    """Initialize Firebase Admin SDK (safe to call multiple times)."""
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token: str) -> dict:
    """
    Verifies the Firebase ID token sent from the frontend.
    Returns the decoded token payload including uid, email, role claim.
    Raises an exception if token is invalid or expired.
    """
    decoded = auth.verify_id_token(id_token)
    return decoded

def get_firestore_client():
    """
    Returns Firestore database client
    """
    return firestore.client()

def get_auth_client():
    """
    Returns Firebase Auth client
    """
    return auth