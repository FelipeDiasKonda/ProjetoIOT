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
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Rota para buscar dados do Firebase
@app.route('/dados', methods=['GET'])
def fetch_data_from_firebase():
    """Buscar dados do Firebase e gerar gráfico."""
    ref = get_database_reference()
    data = ref.get()
    if not data:
        return jsonify({"message": "Nenhum dado encontrado"}), 404

    # Filtrar apenas dados de temperatura
    results = [
        {
            "sensor": value.get("sensor"),
            "value": value.get("value"),
            "unit": value.get("unit"),
            "timestamp": value.get("timestamp")
        }
        for value in data.items() if value.get("sensor") == "temperature"
    ]

    if not results:
        return jsonify({"message": "Nenhum dado de temperatura encontrado"}), 404

    # Extrair timestamps e valores para o gráfico
    timestamps = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r["timestamp"])) for r in results]
    values = [r["value"] for r in results]

    # Gerar gráfico
    fig, ax = plt.subplots()
    ax.plot(timestamps, values, label="Temperatura", color='tab:blue')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Temperatura (°C)')
    ax.set_title('Gráfico de Temperatura')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Salvar gráfico em uma imagem base64 para o frontend
    img_stream = io.BytesIO()
    fig.savefig(img_stream, format='png')
    img_stream.seek(0)
    image_data = base64.b64encode(img_stream.getvalue()).decode('utf-8')

    return render_template('index.html', image_data=image_data)

# Rota para gerar gráfico
@app.route('/grafico', methods=['GET'])
def plot_data():
    ref = get_database_reference()
    data = ref.get()
    if not data:
        return jsonify({"message": "Nenhum dado disponível para gerar gráfico"}), 404

    # Extrair timestamps e valores
    timestamps, values = [], []
    for key, value in data.items():
        if value.get("sensor") == "temperature":
            timestamps.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value.get("timestamp"))))
            values.append(float(value.get("value")))

    if not values:
        return jsonify({"message": "Nenhum dado de temperatura disponível"}), 404

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

    # Retornar a imagem para o frontend
    return render_template('index.html', image_data=image_base64)

# Função para rodar o MQTT em um processo separado
def run_mqtt():
    client = setup_mqtt()
    client.loop_forever()

if __name__ == "__main__":
    matplotlib.use('Agg')
    multiprocessing.set_start_method('spawn', force=True)
    # Inicie o MQTT em um processo separado
    mqtt_process = Process(target=run_mqtt)
    mqtt_process.start()

    print("Processo MQTT iniciado:", mqtt_process.is_alive())

    # Rode o Flask
    app.run(debug=True, use_reloader=False)