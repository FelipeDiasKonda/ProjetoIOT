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
    """Buscar dados do Firebase."""
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

    return jsonify(results)

# Rota para gerar gráfico
@app.route('/grafico', methods=['GET'])
def plot_data():
    """Gerar um gráfico com os dados do Firebase."""
    ref = get_database_reference()
    data = ref.get()
    if not data:
        return jsonify({"message": "Nenhum dado disponível para gerar gráfico"}), 404

    # Extrair timestamps e valores
    timestamps, values = [], []
    for value in data.items():
        if value.get("sensor") == "temperature":
            timestamps.append(value.get("timestamp"))
            values.append(value.get("value"))

    if not values:
        return jsonify({"message": "Nenhum dado de temperatura disponível"}), 404

    # Converter timestamps em formato legível
    timestamps = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)) for ts in timestamps]

    # Retornar dados no formato JSON para o frontend
    return jsonify({
        "timestamps": timestamps,
        "values": values
    })

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