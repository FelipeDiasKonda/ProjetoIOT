import time
import json
import paho.mqtt.client as mqtt
import mysql.connector
from datetime import datetime, timedelta, timezone

def save_to_mysql(data):
    """Salvar dados no MySQL."""
    try:
        connection = mysql.connector.connect(
            host="mysql",  # Nome do serviço MySQL no Docker Compose
            user="root",
            password="example",
            database="weather_data"
        )
        cursor = connection.cursor()
        query = """
            INSERT INTO sensor_data (
                rain_level,
                average_wind_speed,
                wind_direction,
                humidity,
                uv_index,
                solar_radiation,
                temperature,
                timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                rain_level = VALUES(rain_level),
                average_wind_speed = VALUES(average_wind_speed),
                wind_direction = VALUES(wind_direction),
                humidity = VALUES(humidity),
                uv_index = VALUES(uv_index),
                solar_radiation = VALUES(solar_radiation),
                temperature = VALUES(temperature)
        """
        cursor.execute(query, (
            data.get("rain_level", {}).get("value"),
            data.get("average_wind_speed", {}).get("value"),
            data.get("wind_direction", {}).get("value"),
            data.get("humidity", {}).get("value"),
            data.get("uv_index", {}).get("value"),
            data.get("solar_radiation", {}).get("value"),
            data.get("temperature", {}).get("value"),
            data.get("timestamp")
        ))
        connection.commit()
        print("Dados salvos no MySQL:", data)
    except mysql.connector.Error as e:
        print(f"Erro ao salvar dados no MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[INFO] Conexão bem-sucedida ao broker MQTT!")
        if not userdata.get('subscribed', False):
            print("[INFO] Inscrevendo-se no tópico 'konda'...")
            client.subscribe("konda")
            userdata['subscribed'] = True
        else:
            print("[INFO] Já inscrito no tópico.")
    else:
        print(f"[ERRO] Falha na conexão ao broker MQTT. Código: {rc}")


def on_message(client, userdata, msg):
    print(f"[DEBUG] Mensagem recebida no tópico: {msg.topic}")
    print(f"[DEBUG] Payload bruto: {msg.payload.decode()}")

    try:
        payload = json.loads(msg.payload.decode())
        print("[DEBUG] Payload decodificado com sucesso.")

        if isinstance(payload, list):
            data_to_save = {}
            for item in payload:
                label = item.get("n")
                value = item.get("v")
                unit = item.get("u")
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
                elif label == "emw_temperature":
                    data_to_save["temperature"] = {"value": value, "unit": unit}
            
            if data_to_save:
                data_to_save["timestamp"] = time.time()
                print("[DEBUG] Dados extraídos do payload:", data_to_save)
                save_to_mysql(data_to_save)
            else:
                print("[DEBUG] Nenhum dado válido encontrado no payload.")
        else:
            print("[WARN] Payload recebido não é uma lista.")
    except json.JSONDecodeError as e:
        print(f"[ERRO] Erro ao decodificar JSON: {e}")
        print(f"[ERRO] Payload bruto:", msg.payload.decode())
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao processar mensagem MQTT: {e}")


# ... [tudo acima igual, sem alterações]

def on_disconnect(client, userdata, rc):
    """Callback chamada ao desconectar do broker MQTT."""
    print(f"[DISCONNECT] Desconectado do broker MQTT. Código: {rc}")
    if rc != 0:
        print("[DISCONNECT] Desconexão inesperada. Tentando reconectar...")

def setup_mqtt():
    """Configurar e iniciar o cliente MQTT."""
    client = mqtt.Client(protocol=mqtt.MQTTv311, transport="tcp")
    client.user_data_set({'subscribed': False})
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    while True:
        try:
            print("[MQTT] Tentando conectar ao broker MQTT...")
            client.connect("192.168.1.110", 1883, keepalive=60)
            print("[MQTT] Conectado ao broker com sucesso.")
            return client
        except Exception as e:
            print(f"[ERRO] Falha ao conectar ao broker MQTT: {e}")
            print("[INFO] Tentando novamente em 5 segundos...")
            time.sleep(5)

if __name__ == '__main__':
    client = setup_mqtt()
    print("[START] Iniciando conexão MQTT:")
    if client:
        print("[INFO] Cliente MQTT iniciado...")
        client.loop_start()  # Loop MQTT rodando em thread separada

        while True:
            try:
                time.sleep(10)

                if not client.is_connected():
                    print("[MONITOR] Cliente MQTT desconectado. Tentando reconectar...")
                    try:
                        client.reconnect()
                        print("[MONITOR] Reconectado com sucesso!")
                    except Exception as e:
                        print(f"[MONITOR] Falha na tentativa de reconexão: {e}")

            except Exception as e:
                print(f"[FATAL] Erro inesperado no loop principal: {e}")
    else:
        print("[ERRO] Falha ao iniciar o cliente MQTT.")
