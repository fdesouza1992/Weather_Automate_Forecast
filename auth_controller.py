from firebase_admin import auth
from firebase_config import db

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


