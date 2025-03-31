FROM python:3.11-alpine

# Definições para evitar cache excessivo
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalando dependências do sistema
RUN apk add --no-cache \
    build-base \
    linux-headers \
    mariadb-connector-c-dev

# Instalando dependências do Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiando código da aplicação
COPY . .

# Comando de execução com Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
