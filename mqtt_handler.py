import time
import json
import paho.mqtt.client as mqtt
from firebase_setup import get_database_reference

def send_to_firebase(data):
    """Enviar dados para o Firebase."""
    try:
        ref = get_database_reference()
        ref.push(data)
        print("Dados enviados ao Firebase:", data)
    except Exception as e:
        print(f"Erro ao enviar dados para o Firebase: {e}")

def on_connect(client, userdata, flags, rc):
    """Callback chamada ao conectar ao broker MQTT."""
    if rc == 0:
        print("Conexão bem-sucedida ao broker MQTT!")
        client.subscribe("TESTE")  # Substitua pelo tópico correto
    else:
        print(f"Falha na conexão ao broker MQTT. Código de retorno: {rc}")

def on_message(client, userdata, msg):
    """Callback chamada ao receber uma mensagem no MQTT."""
    try:
        # Decodificar a mensagem recebida
        payload = json.loads(msg.payload.decode())
        print("Dados recebidos do MQTT:", payload)

        # Verificar se o payload é uma lista
        if isinstance(payload, list):
            # Processar cada item na lista
            for item in payload:
                # Verificar se o dado refere-se à temperatura (unidade Cel)
                if item.get("u") == "Cel" and "v" in item:
                    data = {
                        "sensor": "temperature",  # Nome fixo para o tipo de dado
                        "value": item["v"],       # Valor da temperatura
                        "unit": item["u"],        # Unidade (Cel)
                        "timestamp": time.time()  # Timestamp atual
                    }
                    send_to_firebase(data)
                    break  # Processar apenas o primeiro dado de temperatura encontrado
        else:
            # Adicione aqui um debug para entender o formato do payload
            print("Payload recebido não é uma lista. Conteúdo:", payload)
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON:", msg.payload.decode())
    except Exception as e:
        print(f"Erro ao processar mensagem MQTT: {e}")

def setup_mqtt():
    """Configurar e iniciar o cliente MQTT."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print("Tentando conectar ao broker MQTT...")
        client.connect("192.168.1.104", 1883, 10)  # Substitua pelo endereço do broker
    except Exception as e:
        print(f"Erro ao conectar ao broker MQTT: {e}")
        return None

    return client

if __name__ == '__main__':
    client = setup_mqtt()
    if client:
        print("Cliente MQTT iniciado...")
        client.loop_forever()
    else:
        print("Falha ao iniciar o cliente MQTT.")
