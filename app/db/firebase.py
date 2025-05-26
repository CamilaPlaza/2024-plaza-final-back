import json
from dotenv import load_dotenv
import os
from firebase_admin import credentials, firestore, initialize_app

# Cargar variables de entorno
load_dotenv()

def init_firebase():
    cred_file_path = os.getenv("FIREBASE_CRED_PATH")
    with open(cred_file_path) as f:
        firebase_creds_dict = json.load(f)
    cred = credentials.Certificate(firebase_creds_dict)
    initialize_app(cred)
    return firestore.client()

db = init_firebase()
