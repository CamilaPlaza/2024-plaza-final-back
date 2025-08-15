# app/db/firebase.py
import os, json
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    # Evitar doble inicialización si algún import lo ejecuta dos veces
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CRED_PATH")
        if not cred_path:
            raise RuntimeError("FIREBASE_CRED_PATH no está seteada en el entorno (.env)")

        # Resolver a ruta absoluta por las dudas
        if not os.path.isabs(cred_path):
            cred_path = os.path.abspath(cred_path)

        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"No existe el archivo de credenciales: {cred_path}")

        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Error leyendo JSON de credenciales: {e}")

        cred = credentials.Certificate(data)
        firebase_admin.initialize_app(cred)

    # Si ya había app inicializada, solo devolvés el cliente
    return firestore.client()

db = init_firebase()
