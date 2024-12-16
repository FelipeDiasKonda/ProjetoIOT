# Use uma imagem base leve
FROM python:3.9-slim

# Configure o diretório de trabalho
WORKDIR /app

# Copie o arquivo de dependências
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie os arquivos da aplicação
COPY . .  
# Exponha a porta usada pelo Flask
EXPOSE 80

# Configure o comando padrão
CMD ["python", "app.py"]

