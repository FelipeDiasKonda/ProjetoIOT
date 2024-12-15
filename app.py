import time
import matplotlib
from flask import Flask, jsonify, render_template
import matplotlib.pyplot as plt
import io
import base64
import multiprocessing
from multiprocessing import Process 
import mqtt_handler as mqtt_handler  # Importa o arquivo mqtt_handler.py
from mqtt_handler import setup_mqtt
import math
import mysql.connector
app = Flask(__name__)

def rad_to_direction_with_icon(rad):
    """Converte radianos para direção cardeal e retorna ícone correspondente."""
    directions = [
        ('Norte', 'rotate-0'),    # Norte
        ('Nordeste', 'rotate-45'),  # Nordeste
        ('Leste', 'rotate-90'),   # Leste
        ('Sudeste', 'rotate-135'), # Sudeste
        ('Sul', 'rotate-180'),  # Sul
        ('Sudoeste', 'rotate-225'), # Sudoeste
        ('Oeste', 'rotate-270'),  # Oeste
        ('Noroeste', 'rotate-315')  # Noroeste
    ]
    rad = rad % (2 * math.pi)
    index = int((rad + math.pi / 8) // (math.pi / 4)) % 8
    return directions[index]

def get_rain_status(rain_level):
    """Determina o status da chuva com base no nível acumulado."""
    if rain_level < 0.7764:
        return "Sem chuva"
    elif rain_level < 0.7770:
        return "Chuviscando"
    else :
        return "Chovendo"


def get_uv_status(uv_index):
    """Determina o status da radiação UV."""
    if uv_index < 3:
        return "Níveis baixos de UV"
    elif uv_index < 6:
        return "Níveis moderados de UV"
    elif uv_index < 8:
        return "Níveis altos de UV"
    elif uv_index < 11:
        return "Níveis muito altos de UV"
    else:
        return "Risco extremo de UV"

def get_humidity_status(humidity):
    """Determina o status da umidade."""
    if humidity < 30:
        return "Ar muito seco"
    elif humidity < 60:
        return "Umidade confortável"    
    else:
        return "Ar muito úmido"

def get_temperature_status(temperature):
    """Determina o status da temperatura."""
    if temperature < 10:
        return "Frio intenso"
    elif temperature < 20:
        return "Clima frio"
    elif temperature < 30:
        return "Clima agradável"
    elif temperature < 40:
        return "Clima quente"
    else:
        return "Calor extremo"
    
def get_mysql_data():
    """Buscar dados do MySQL."""
    connection = None  # Inicializar connection como None
    cursor = None      # Inicializar cursor como None
    try:
        connection = mysql.connector.connect(
            host="mysql",  # Nome do serviço MySQL no Docker Compose
            user="root",
            password="example",
            database="weather_data"
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"Erro ao buscar dados do MySQL: {e}")
        return None
    finally:
        # Fechar cursor e conexão somente se foram abertos
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route('/')
def index():
    data = get_mysql_data()

    if not data:
        # Passar valores padrão ao template
        return render_template(
            'index.html', 
            message="Nenhum dado disponível no momento.",
            wind_direction="N/D",
            wind_icon_class="rotate-0",
            uv_status="N/A",
            humidity_status="N/A",
            rain_status="N/A",
            temperature_status="N/A",
            temperature=0,
            uv_index=0,
            humidity=0,
            rain_level=0
        )

    # Dados dos sensores
    wind_direction_rad = float(data.get('wind_direction', 0))
    uv_index = float(data.get('uv_index', 0))
    humidity = float(data.get('humidity', 0))
    rain_level = float(data.get('rain_level', 0))
    temperature = float(data.get('temperature', 0))

    # Converter radianos para direção cardeal e ícone
    wind_direction, wind_icon_class = rad_to_direction_with_icon(wind_direction_rad)

    # Mensagens baseadas nos valores
    rain_status = get_rain_status(rain_level)
    uv_status = get_uv_status(uv_index)
    humidity_status = get_humidity_status(humidity)
    temperature_status = get_temperature_status(temperature)

    return render_template(
        'index.html',
        wind_direction=wind_direction,
        wind_icon_class=wind_icon_class,
        uv_status=uv_status,
        humidity_status=humidity_status,
        rain_status=rain_status,
        temperature_status=temperature_status,
        temperature=temperature,
        uv_index=uv_index,
        humidity=humidity,
        rain_level=rain_level
    )


# Rota para buscar dados do Firebase
@app.route('/dados', methods=['GET'])
def dashboard():
    """Rota principal para exibir o dashboard com gráficos interativos."""
    try:
        connection = mysql.connector.connect(
            host="mysql",  # Nome do serviço MySQL no Docker Compose
            user="root",
            password="example",
            database="weather_data"
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT timestamp, temperature, humidity, rain_level FROM sensor_data ORDER BY timestamp")
        data = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Erro ao buscar dados do MySQL: {e}")
        return jsonify({"message": "Erro ao buscar dados do MySQL"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    if not data:
        return render_template('dashboard.html', message="Nenhum dado disponível no momento.")

    sensor_data = {"temperature": [], "humidity": [], "rain_level": [], "timestamps": []}
    for row in data:
        timestamp = row["timestamp"]
        if timestamp:
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            sensor_data["timestamps"].append(formatted_time)
        sensor_data["temperature"].append(row["temperature"])
        sensor_data["humidity"].append(row["humidity"])
        sensor_data["rain_level"].append(row["rain_level"])

    return render_template('dashboard.html', sensor_data=sensor_data)

# Rota para gerar gráfico
@app.route('/temperatura', methods=['GET'])
def plot_data():
    try:
        connection = mysql.connector.connect(
            host="mysql",  # Nome do serviço MySQL no Docker Compose
            user="root",
            password="example",
            database="weather_data"
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sensor_data WHERE temperature IS NOT NULL ORDER BY timestamp")
        data = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Erro ao buscar dados do MySQL: {e}")
        return jsonify({"message": "Erro ao buscar dados do MySQL"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    if not data:
        return jsonify({"message": "Nenhum dado disponível para gerar gráfico"}), 404

    # Extrair timestamps e valores
    timestamps, values = [], []
    for row in data:
        timestamp = row.get('timestamp')
        temperature = row.get('temperature')
        if timestamp and temperature is not None:
            timestamps.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)))
            values.append(float(temperature))

    if not values:
        return jsonify({"message": "Nenhum dado de temperatura disponível"}), 404

    # Calcular últimas temperaturas, média, máximo e mínimo
    last_temperature = values[-1]
    average_temperature = sum(values) / len(values)
    max_temperature = max(values)
    min_temperature = min(values)

    # Criar o gráfico
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, values, marker='o', linestyle='-', color='b')
    plt.xlabel('Timestamp')
    plt.ylabel('Temperatura')
    plt.title('Gráfico de Temperatura')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Salvar o gráfico em um buffer de memória
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    # Preparar os dados para exibir no template
    temperature_data = [{"timestamp": ts, "value": val} for ts, val in zip(timestamps, values)]

    # Retornar a imagem e dados para o frontend
    return render_template('temp.html', 
                           image_data=image_base64, 
                           last_temperature=last_temperature,
                           average_temperature=average_temperature,
                           max_temperature=max_temperature,
                           min_temperature=min_temperature,
                           temperature_data=temperature_data)

# Função para rodar o MQTT em um processo separado
def run_mqtt():
    client = setup_mqtt()
    if client:
        client.loop_forever()
    else:
        print("Erro: Cliente MQTT não foi inicializado corretamente.")

if __name__ == "__main__":
    matplotlib.use('Agg')
    multiprocessing.set_start_method('spawn', force=True)
    # Inicie o MQTT em um processo separado
    mqtt_process = Process(target=run_mqtt)
    mqtt_process.start()

    print("Processo MQTT iniciado:", mqtt_process.is_alive())

    # Rode o Flask
    app.run(debug=True, host='0.0.0.0', port=80)
