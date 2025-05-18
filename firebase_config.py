import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase Admin SDK
key_path = os.getenv("FIREBASE_KEY_PATH")
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

# Initialize Firestore reference
db = firestore.client()

