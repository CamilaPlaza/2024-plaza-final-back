# app/db/firebase.py
import os, json
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    if firebase_admin._apps:
        return firestore.client()

    json_env = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if json_env:
        try:
            if isinstance(json_env, str):
                data = json.loads(json_env)
            else:
                data = json_env
            cred = credentials.Certificate(data)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            raise RuntimeError(f"FIREBASE_CREDENTIALS_JSON inválida: {e}")

    cred_path = os.getenv("FIREBASE_CRED_PATH")
    if cred_path:
        if not os.path.isabs(cred_path):
            cred_path = os.path.abspath(cred_path)
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"No existe el archivo de credenciales: {cred_path}")
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cred = credentials.Certificate(data)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            raise RuntimeError(f"Error leyendo JSON de credenciales desde archivo: {e}")

    raise RuntimeError(
        "Faltan credenciales de Firebase. Seteá FIREBASE_CREDENTIALS_JSON en Render."
    )

db = init_firebase()
