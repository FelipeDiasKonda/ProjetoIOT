# Use a imagem base do Python
FROM python:3.9-slim

# Configure o diretório de trabalho
WORKDIR /app

# Copie apenas o arquivo de dependências primeiro (para melhor cache de camadas)
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante dos arquivos (opcional para produção, desnecessário em dev)
# COPY . .

# Configure o ponto de entrada para a aplicação
CMD ["python", "app.py"]
