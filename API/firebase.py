import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase
cred = credentials.Certificate('smartaccess-ca7da-firebase-adminsdk-6zbw4-c8fba4e278.json')
firebase_admin.initialize_app(cred, {'databaseURL': "https://smartaccess-ca7da-default-rtdb.firebaseio.com"})

def send_data_to_firebase(license_plate: str):
    try:
        ref = db.reference()
        print("Sending data to Firebase: ", license_plate)

        ref.child("license_plate").set(license_plate)  
        
        return {"status": "success" , "message": "Data sent to Firebase"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
