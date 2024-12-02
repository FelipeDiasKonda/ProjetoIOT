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
        client.subscribe("konda")  # Substitua pelo tópico correto
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
            # Inicializar estrutura para dados selecionados
            data_to_save = {}

            # Processar cada item na lista
            for item in payload:
                label = item.get("n")
                value = item.get("v")
                unit = item.get("u")

                # Verificar e armazenar as labels desejadas
                if label == "emw_rain_level":
                    data_to_save["rain_level"] = {"value": value, "unit": unit}
                elif label == "emw_average_wind_speed":
                    data_to_save["average_wind_speed"] = {"value": value, "unit": unit}
                elif label == "emw_wind_direction":
                    data_to_save["wind_direction"] = {"value": value, "unit": unit}
                elif label == "emw_humidity":
                    data_to_save["humidity"] = {"value": value, "unit": unit}
                elif label == "emw_uv":
                    data_to_save["uv_index"] = {"value": value, "unit": unit}
                elif label == "emw_solar_radiation":
                    data_to_save["solar_radiation"] = {"value": value, "unit": unit}
                elif unit == "Cel":
                    data_to_save["temperature"] = {"value": value, "unit": unit}

            # Verificar se há dados para salvar
            if data_to_save:
                data_to_save["timestamp"] = time.time()
                send_to_firebase(data_to_save)
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
        print("Falha ao iniciar o cliente MQTT. Verifique o broker e a conexão de rede.")
