import firebase_admin
from firebase_admin import credentials, db
import time

def setup_firebase():
    """Configura o Firebase."""
    cred = credentials.Certificate("projetoiot-816bb-firebase-adminsdk-51dcx-f7d69da51d.json")  # Substitua pelo seu arquivo JSON
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
            "n": "Cel",
            "v": 22.5,  # Temperatura em °C
            "u": "Cel"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 10,
            "n": "emw_rain_level",
            "v": 0.12,  # Nível de chuva em metros
            "u": "m"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 20,
            "n": "emw_average_wind_speed",
            "v": 3.5,  # Velocidade média do vento em m/s
            "u": "m/s"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 30,
            "n": "emw_wind_direction",
            "v": 1.57,  # Direção do vento em radianos
            "u": "rad"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 40,
            "n": "emw_humidity",
            "v": 85.0,  # Umidade relativa em %
            "u": "%RH"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 50,
            "n": "emw_uv",
            "v": 3.2,  # Índice UV
            "u": "/"
        },
        {
            "bn": "BC33ACFFFEF41AD6",
            "bt": int(time.time()) + 60,
            "n": "emw_solar_radiation",
            "v": 150.0,  # Radiação solar em W/m²
            "u": "W/m2"
        }
    ]

    for data in example_data:
        ref.push(data)  # Inserir os dados no Firebase
        print(f"Dado inserido no Firebase: {data}")

# Inicializar o Firebase ao importar este módulo
setup_firebase()

# Adicionar dados de exemplo ao banco
#add_example_data()
