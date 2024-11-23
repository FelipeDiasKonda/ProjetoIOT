import time
import json
import paho.mqtt.client as mqtt
from firebase_setup import get_database_reference

def send_to_firebase(data):
    """Enviar dados para o Firebase."""
    ref = get_database_reference()
    ref.push(data)
    print("Dados enviados ao Firebase:", data)

def on_message(client, userdata, msg):
    """Callback chamada ao receber uma mensagem no MQTT."""
    try:
        payload = json.loads(msg.payload.decode())
        print("Dados recebidos do MQTT:", payload)

        # Apenas processar dados de temperatura
        if payload.get("n") == "temperature":
            data = {
                "sensor": payload.get("n"),
                "value": payload.get("v"),
                "unit": payload.get("u"),
                "timestamp": time.time()
            }
            send_to_firebase(data)
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON:", msg.payload.decode())

def setup_mqtt():
    """Configurar e iniciar o cliente MQTT."""
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("192.168.1.104", 1883, 10)  # Substitua pelo seu broker MQTT
    client.subscribe("TESTE")     # Substitua pelo tópico MQTT
    return client

if __name__ == '__main__':
    client = setup_mqtt()
    print("Cliente MQTT iniciado...")
    client.loop_forever()
