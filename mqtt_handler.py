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

        # Inserir dados no banco de dados
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
    """Callback chamada ao conectar ao broker MQTT."""
    if rc == 0:
        print("Conexão bem-sucedida ao broker MQTT!")
        if not userdata.get('subscribed', False):  # Verifica se já está inscrito
            client.subscribe("konda")  # Substitua pelo tópico correto
            userdata['subscribed'] = True
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
                elif label == "emw_temperature":
                    data_to_save["temperature"] = {"value": value, "unit": unit}

            # Verificar se há dados para salvar
            if data_to_save:
                data_to_save["timestamp"] = time.time()
                save_to_mysql(data_to_save)
        else:
            # Adicione aqui um debug para entender o formato do payload
            print("Payload recebido não é uma lista.\n")
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON:", msg.payload.decode())
    except Exception as e:
        print(f"Erro ao processar mensagem MQTT: {e}")

def setup_mqtt():
    """Configurar e iniciar o cliente MQTT."""
    client = mqtt.Client(userdata={'subscribed': False})
    client.on_connect = on_connect
    client.on_message = on_message

    while True:  # Loop para reconexão automática
        try:
            print("Tentando conectar ao broker MQTT...")
            client.connect("192.168.1.110", 1883, keepalive=700)  
            return client
        except Exception as e:
            print(f"Erro ao conectar ao broker MQTT: {e}. Tentando novamente em 5s...")
            time.sleep(5)
        

if __name__ == '__main__':
    client = setup_mqtt()
    if client:
        print("Cliente MQTT iniciado...")
        client.loop_start()  # Mantém a conexão ativa em segundo plano

        while True:
            try:
                time.sleep(10)  # Mantém o programa rodando
                if not client.is_connected():
                    print("Cliente MQTT desconectado! Tentando reconectar...")
                    client.reconnect()
            except Exception as e:
                print(f"Erro inesperado: {e}")
    else:
        print("Falha ao iniciar o cliente MQTT. Verifique o broker e a conexão de rede.")
