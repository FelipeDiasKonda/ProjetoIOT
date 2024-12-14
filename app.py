import time
import matplotlib
from flask import Flask, jsonify, render_template
import matplotlib.pyplot as plt
import io
import base64
from firebase_setup import get_database_reference
import multiprocessing
from multiprocessing import Process 
import mqtt_handler as mqtt_handler  # Importa o arquivo mqtt_handler.py
from mqtt_handler import setup_mqtt
import math
app = Flask(__name__)

def rad_to_direction_with_icon(rad):
    """Converte radianos para direção cardeal e retorna ícone correspondente."""
    directions = [
        ('N', 'rotate-0'),    # Norte
        ('NE', 'rotate-45'),  # Nordeste
        ('E', 'rotate-90'),   # Leste
        ('SE', 'rotate-135'), # Sudeste
        ('S', 'rotate-180'),  # Sul
        ('SW', 'rotate-225'), # Sudoeste
        ('W', 'rotate-270'),  # Oeste
        ('NW', 'rotate-315')  # Noroeste
    ]
    rad = rad % (2 * math.pi)
    index = int((rad + math.pi / 8) // (math.pi / 4)) % 8
    return directions[index]

def get_rain_status(rain_level):
    """Determina o status da chuva com base no nível acumulado."""
    if rain_level < 1:
        return "Sem chuva"
    elif rain_level < 2.5:
        return "Chuviscando"
    elif rain_level < 7.6:
        return "Chuva moderada"
    else:
        return "Chuva forte"

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
@app.route('/')
def index():
    ref = get_database_reference()
    data = ref.get()

    if not data:
        return render_template('index.html', message="Nenhum dado disponível no momento.")

    # Dados dos sensores
    wind_direction_rad = 0
    uv_index = 0
    humidity = 0
    rain_level = 0
    temperature = 0

    # Verificar e extrair os valores mais recentes
    for key, value in data.items():
        if 'wind_direction' in value:
            wind_direction_rad = float(value['wind_direction'].get('value', 0))
        if 'uv_index' in value:
            uv_index = float(value['uv_index'].get('value', 0))
        if 'humidity' in value:
            humidity = float(value['humidity'].get('value', 0))
        if 'rain_level' in value:
            rain_level = float(value['rain_level'].get('value', 0))
        if 'temperature' in value:
            temperature = float(value['temperature'].get('value', 0))

    # Converter radianos para direção cardeal e ícone
    wind_direction, wind_icon_class = rad_to_direction_with_icon(wind_direction_rad)

    # Mensagens baseadas nos valores
    rain_status = get_rain_status(rain_level)
    uv_status = get_uv_status(uv_index)
    humidity_status = get_humidity_status(humidity)
    temperature_status = get_temperature_status(temperature)

    return render_template('index.html', 
                           wind_direction=wind_direction,
                           wind_icon_class=wind_icon_class,
                           uv_status=uv_status, 
                           humidity_status=humidity_status, 
                           rain_status=rain_status,
                           temperature_status=temperature_status,
                           temperature=temperature,
                           uv_index=uv_index,
                           humidity=humidity,
                           rain_level=rain_level)

# Rota para buscar dados do Firebase
@app.route('/dados', methods=['GET'])
def dashboard():
    """Rota principal para exibir o dashboard com gráficos interativos."""
    ref = get_database_reference()
    data = ref.get()

    if not data:
        return render_template('dashboard.html', message="Nenhum dado disponível no momento.")

    # Organizar os dados para gráficos
    sensor_data = {"temperature": [], "humidity": [], "rain_level": [], "timestamps": []}
    for key, value in data.items():
        timestamp = value.get("timestamp")
        if timestamp:
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            sensor_data["timestamps"].append(formatted_time)
        
        # Adicionar os valores dos sensores
        for sensor_key in ["temperature", "humidity", "rain_level"]:
            sensor_value = value.get(sensor_key, {}).get("value")
            sensor_data[sensor_key].append(float(sensor_value) if sensor_value else None)

    return render_template('dashboard.html', sensor_data=sensor_data)
# Rota para gerar gráfico
@app.route('/temperatura', methods=['GET'])
def plot_data():
    ref = get_database_reference()
    data = ref.get()
    if not data:
        return jsonify({"message": "Nenhum dado disponível para gerar gráfico"}), 404

    # Extrair timestamps e valores
    timestamps, values = [], []
    for key, value in data.items():
        # Acessar a chave "temperature" que está dentro de cada item
        temperature_data = value.get("temperature", {})
        timestamp = value.get("timestamp")
        
        # Verificar se a chave "temperature" existe
        if temperature_data:
            temp_value = temperature_data.get("value")
            
            # Verificar se os dados de timestamp e valor de temperatura existem
            if timestamp and temp_value is not None:
                # Adicionar o timestamp formatado e o valor da temperatura
                timestamps.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)))
                values.append(float(temp_value))

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
