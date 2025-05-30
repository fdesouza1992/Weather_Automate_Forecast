from firebase_admin import auth
from firebase_config import db
from dotenv import load_dotenv
import os
import requests
import json

# Load environment variables
load_dotenv()

# Function to create a new user
def create_user(email="", password="", phone_number="", display_name=""):
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            phone_number=phone_number
        )
        uid = user.uid
        print(f"✅ Successfully created user: {uid}")

        # Save profile data in Firestore under /users/{uid}
        profile_data = {
            "phone": phone_number,
            "email": email,
            "name": display_name,
            "address": {
                "street": "",
                "city": "",
                "state": "",
                "zipCode": "",
                "country": ""
            },
            "password": password,
            "export_as_post": [],
            "export_as_story": [],
            "favorite_cities": [],
            "friends": [],
            "previously_used_passwords": []
        }

        db.collection('users').document(uid).set(profile_data)
        print(f"Successfully saved user profile data in Firestore: {uid}")

        return uid
    
    except Exception as e:
        print(f"Error creating user: {e}")
        return None
    
# Function to delete a user
def delete_user(uid):
    try:
        auth.delete_user(uid)
        print(f"Successfully deleted user: {uid}")
    except Exception as e:
        print(f"Error deleting user: {e}")
        return None

# Verify user credentials using Firebase REST API. Returns: tuple of (uid, error_message
def verify_password(email, password):
    web_api_key = os.getenv("FIREBASE_WEB_API_KEY")
    if not web_api_key:
        return None, "Firebase Web API key not configured in .env file"
    
    try:
        # Firebase REST API endpoint
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={web_api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code == 200:
            return data.get('localId'), None  # Return user ID
        else:
            error_msg = data.get('error', {}).get('message', 'Unknown error occurred')
            return None, error_msg
            
    except Exception as e:
        return None, str(e)


def send_password_reset_email_rest(email):
    firebase_api_key = os.getenv("FIREBASE_API_KEY")  # Must be in your .env file
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={firebase_api_key}"
    payload = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return True, None
    else:
        return False, response.json().get("error", {}).get("message", "Unknown error")


# verify if the user exists
#def verify_id_token(token):
#    try:
#        decoded_token = auth.verify_id_token(token)
#        uid = decoded_token['uid']
#        print(f"Token is valid. User ID: {uid}")
#        return uid
#    except Exception as e:
#       print(f"Error verifying token: {e}")
#        return None


