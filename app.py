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
    rain_status = "Está seco" if rain_level < 0.2 else "Está chovendo"
    uv_status = "Dia nublado" if uv_index < 3 else "Dia ensolarado"
    humidity_status = "Lembre-se de tomar água" if humidity < 40 else "Humidade normal"
    temperature_status = "Está frio" if temperature < 20 else "Está quente"

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
def fetch_all_graphs():
    """Buscar dados do Firebase e gerar gráficos para todos os sensores."""
    ref = get_database_reference()
    data = ref.get()

    if not data:
        return jsonify({"message": "Nenhum dado encontrado"}), 404

    # Organizar os dados por tipo de sensor
    sensor_data = {}
    for key, value in data.items():
        # Acessar o tipo de sensor diretamente pelas chaves específicas
        for sensor_key in ['temperature', 'humidity', 'rain_level', 'solar_radiation', 'uv_index', 'wind_direction', 'wind_speed']:
            sensor_value = value.get(sensor_key)
            timestamp = value.get('timestamp')

            # Verificar se o valor do sensor e o timestamp existem
            if sensor_value is not None and timestamp:
                # Se o sensor_value for um dicionário, tente acessar o valor correto
                if isinstance(sensor_value, dict):
                    sensor_value = sensor_value.get('value')

                # Se não tiver dados para esse sensor, inicializa
                if sensor_key not in sensor_data:
                    sensor_data[sensor_key] = {"timestamps": [], "values": [], "unit": value.get('u', 'Unidade não definida')}

                # Adicionar os dados
                sensor_data[sensor_key]["timestamps"].append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)))
                try:
                    sensor_data[sensor_key]["values"].append(float(sensor_value))  # Tentar converter para float
                except ValueError:
                    continue  # Se não conseguir converter, simplesmente ignore

    if not sensor_data:
        return jsonify({"message": "Nenhum dado de sensores encontrado"}), 404

    # Gerar gráficos para cada sensor
    graphs = {}
    for sensor, data in sensor_data.items():
        timestamps = data["timestamps"]
        sensor_values = data["values"]
        unit = data["unit"]

        # Criar gráfico
        fig, ax = plt.subplots()
        ax.plot(timestamps, sensor_values, marker='o', label=sensor, color='tab:blue')
        ax.set_xlabel('Timestamp')
        ax.set_ylabel(f'{sensor} ({unit})')
        ax.set_title(f'Gráfico de {sensor}')
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Converter gráfico para base64
        img_stream = io.BytesIO()
        fig.savefig(img_stream, format='png')
        img_stream.seek(0)
        graphs[sensor] = base64.b64encode(img_stream.getvalue()).decode('utf-8')

    return render_template('dashboard.html', graphs=graphs)

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
    app.run(host='0.0.0.0', port=5000, debug=True)
