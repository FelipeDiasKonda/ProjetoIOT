import firebase_admin
from firebase_admin import credentials, db

def setup_firebase():
    """Configura o Firebase."""
    cred = credentials.Certificate("projetoiot-816bb-firebase-adminsdk-51dcx-17cd3df41b.json")  # Substitua pelo seu arquivo JSON
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://projetoiot-816bb-default-rtdb.firebaseio.com/'  # Substitua pela URL do Firebase
    })

def get_database_reference():
    """Retorna a referência para o banco de dados Firebase."""
    return db.reference('sensor_data')

# Inicializar o Firebase ao importar este módulo
setup_firebase()
