import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase Admin SDK
key_path = os.getenv("FIREBASE_KEY_PATH")
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
})

# Initialize Firestore reference
db = firestore.client()

bucket = storage.bucket()
