import json
from firebase_config import db

# Function to upload country codes to Firestore
def upload_country_codes(json_path="country_code_data.json"):
    try:
        with open(json_path, "r") as f:
            country_data = json.load(f)

        for entry in country_data:
            code = entry["code"]
            name = entry["name"]
            doc_ref = db.collection("countries").document(code)
            doc_ref.set({
                "code": code,
                "name": name
            })

        print("Country codes uploaded successfully.")

    except Exception as e:
        print(f"Error uploading country codes: {e}")

# Run the upload
if __name__ == "__main__":
    upload_country_codes()