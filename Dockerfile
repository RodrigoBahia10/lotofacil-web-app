# PASSO 1: Começamos com uma imagem base oficial do Python.
# A tag "slim" é uma versão otimizada e mais leve.
FROM python:3.11-slim

# PASSO 2: Definimos o diretório de trabalho principal dentro do contêiner.
# É como criar uma pasta e entrar nela.
WORKDIR /app

# PASSO 3: Copiamos apenas a nossa "lista de compras" para dentro do contêiner.
# Fazemos isso primeiro por uma questão de otimização de cache do Docker.
COPY requirements.txt .

# PASSO 4: Executamos o pip para instalar todas as bibliotecas da lista.
RUN pip install --no-cache-dir -r requirements.txt

# PASSO 5: Agora copiamos todo o resto do nosso projeto (app.py, pasta templates, etc.)
# para dentro do diretório de trabalho /app do contêiner.
COPY . .

# PASSO 6: Este é o comando que será executado quando o contêiner iniciar.
# Dizemos ao Gunicorn para iniciar e servir nossa aplicação Flask.
# --bind 0.0.0.0:8000: Escute por requisições na porta 8000, vindo de qualquer lugar.
# app:app: No arquivo app.py, encontre a variável 'app' (nossa instância Flask).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "120", "app:app"]