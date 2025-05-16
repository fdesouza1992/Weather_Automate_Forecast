import firebase_admin
from firebase_admin import credentials, auth, firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate('firebase/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Initialize Firestore reference
db = firestore.client()

