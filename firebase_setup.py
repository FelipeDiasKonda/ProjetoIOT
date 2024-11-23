import firebase_admin
from firebase_admin import credentials, db
import time

def setup_firebase():
    """Configura o Firebase."""
    cred = credentials.Certificate("projetoiot-816bb-firebase-adminsdk-51dcx-17cd3df41b.json")  # Substitua pelo seu arquivo JSON
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://projetoiot-816bb-default-rtdb.firebaseio.com/'  # Substitua pela URL do Firebase
    })

def get_database_reference():
    """Retorna a referência para o banco de dados Firebase."""
    return db.reference('sensor_data')

def add_example_data():
    """Adicionar dados de exemplo manualmente para testar."""
    ref = get_database_reference()

    # Dados simulados no formato do seu sensor
    example_data = [
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()),  # Timestamp atual
            "n": "temperature",
            "v": 24.5,  # Temperatura em °C
            "u": "°C"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 10,
            "n": "temperature",
            "v": 25.0,  # Temperatura em °C
            "u": "°C"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 20,
            "n": "temperature",
            "v": 24.7,  # Temperatura em °C
            "u": "°C"
        }
    ]

    for data in example_data:
        ref.push(data)  # Inserir os dados no Firebase

# Inicializar o Firebase ao importar este módulo
setup_firebase()

# Adicionar dados de exemplo ao banco
#add_example_data()
