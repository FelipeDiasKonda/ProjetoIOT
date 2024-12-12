import time
from flask import Flask, jsonify
import matplotlib.pyplot as plt
import io
import base64
from firebase_setup import get_database_reference
import multiprocessing
import mqtt_handler  # Importa o arquivo mqtt_handler.py

app = Flask(__name__)

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
        for key, value in data.items() if value.get("sensor") == "temperature"
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
    for key, value in data.items():
        if value.get("sensor") == "temperature":
            timestamps.append(value.get("timestamp"))
            values.append(value.get("value"))

    if not values:
        return jsonify({"message": "Nenhum dado de temperatura disponível"}), 404

    # Converter timestamps em formato legível
    timestamps = [time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)) for ts in timestamps]

    # Criar gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, values, marker='o')
    plt.title('Temperatura ao longo do tempo')
    plt.xlabel('Horário')
    plt.ylabel('Temperatura (°C)')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    # Salvar gráfico em memória e retornar como base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return f'<img src="data:image/png;base64,{plot_ur}" />'

# Função para rodar o MQTT em um processo separado
def run_mqtt():
    mqtt_handler.start_mqtt()

if __name__ == '__main__':
    # Iniciar MQTT em um processo separado
    mqtt_process = multiprocessing.Process(target=run_mqtt)
    mqtt_process.start()

    # Rodar o Flask
    app.run(debug=True)
