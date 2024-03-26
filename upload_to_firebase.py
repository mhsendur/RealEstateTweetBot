import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json

# Path to the Firebase project's service account key JSON file
cred_path = 'path/to/serviceAccountKey.json'

# Initialize the Firebase app with your project's credentials
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-database-url.firebaseio.com/'  # Replace with the Realtime Database URL
})

# Path to the JSON file that is wanted to upload
json_file_path = 'path/your/data.json'

# Firebase Realtime Database path where you want to upload the data
firebase_db_path = '/your_database_path'

def upload_json_to_firebase(json_path, db_path):
    # Load the JSON data
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    # Get a reference to the database service
    db_ref = db.reference(db_path)
    
    # Set the data at the specified path
    db_ref.set(data)
    
    print(f"Data from {json_path} has been uploaded to Firebase at {db_path}")

if __name__ == '__main__':
    upload_json_to_firebase(json_file_path, firebase_db_path)
