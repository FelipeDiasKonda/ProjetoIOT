# Use a imagem base do Python
FROM python:3.9-slim

# Configure o diretório de trabalho
WORKDIR /app

# Copie os arquivos do projeto para o container
COPY . .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Configure o ponto de entrada
CMD ["python", "app.py"]
