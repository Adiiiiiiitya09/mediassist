import firebase_admin
from firebase_admin import credentials, auth
import os
import logging

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(__file__),
    'intelehealth-172ad-firebase-adminsdk-fbsvc-79eeb9e695.json'
)

def initialize_firebase():
    """Initialize Firebase Admin SDK for Auth only — no Firestore needed."""
    if not firebase_admin._apps:
        if not os.path.exists(SERVICE_ACCOUNT_PATH):
            raise FileNotFoundError(f"Service account JSON not found: {SERVICE_ACCOUNT_PATH}")
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
        logger.info("✓ Firebase Auth initialized")

def verify_firebase_token(id_token: str) -> dict:
    return auth.verify_id_token(id_token)