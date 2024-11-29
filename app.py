import time
import matplotlib
matplotlib.use('Agg')  # Configurar backend antes de importar pyplot
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, jsonify, render_template
from firebase_setup import get_database_reference
import multiprocessing
from multiprocessing import Process 
import mqtt_handler  # Importa o arquivo mqtt_handler.py
from mqtt_handler import setup_mqtt

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Rota para buscar dados do Firebase
@app.route('/dados', methods=['GET'])
def fetch_all_graphs():
    ref = get_database_reference()
    data = ref.get()

    if not data:
        return jsonify({"message": "Nenhum dado encontrado"}), 404

    # Organizar os dados por tipo de sensor
    sensor_data = {}
    for key, value in data.items():
        sensor = value.get("n")
        if not sensor or "bt" not in value or "v" not in value:  # Validação adicional
            continue
        if sensor not in sensor_data:
            sensor_data[sensor] = []
        sensor_data[sensor].append({
            "timestamp": value.get("bt"),
            "value": value.get("v"),
            "unit": value.get("u", "")  # Fornecer uma unidade padrão vazia se não existir
        })

    # Gerar gráficos para cada sensor
    graphs = {}
    for sensor, values in sensor_data.items():
        timestamps = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(v["timestamp"])) for v in values]
        sensor_values = [v["value"] for v in values]
        unit = values[0]["unit"]

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
        plt.close(fig)  # Fechar a figura para liberar memória

    return render_template('dashboard.html', graphs=graphs)

# Rota para gerar gráfico de temperatura
@app.route('/temperatura', methods=['GET'])
def plot_data():
    ref = get_database_reference()
    data = ref.get()
    if not data:
        return jsonify({"message": "Nenhum dado disponível para gerar gráfico"}), 404

    # Extrair timestamps e valores de temperatura
    timestamps, values = [], []
    for key, value in data.items():
        if value.get("n") == "Cel" and "bt" in value and "v" in value:
            timestamp = value.get("bt")
            temp_value = value.get("v")
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
    plt.close()  # Fechar o gráfico

    # Preparar os dados para exibir no template
    temperature_data = [{"timestamp": ts, "value": val} for ts, val in zip(timestamps, values)]

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
        print("MQTT conectado com sucesso")
        client.loop_forever()
    else:
        print("Erro: Cliente MQTT não foi inicializado corretamente.")

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    # Inicie o MQTT em um processo separado
    mqtt_process = Process(target=run_mqtt)
    mqtt_process.start()

    print("Processo MQTT iniciado:", mqtt_process.is_alive())

    try:
        app.run(debug=True, use_reloader=False)
    finally:
        mqtt_process.terminate()
        mqtt_process.join()
