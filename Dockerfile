# Usa a imagem oficial do Python 3.12 baseada em Debian Slim para ser leve e segura
FROM python:3.12-slim

# Define variáveis de ambiente essenciais para o Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Instala dependências do sistema necessárias para compilar pacotes
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Atualiza o pip para a versão mais recente
RUN pip install --no-cache-dir --upgrade pip

# Copia e instala as depências do projeto a partir do arquivo requirements.txt
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código  do backend para dentro do container
COPY backend/ .

# Cria um usuário de sistema sem privilégios (sem senha e sem pasta home) chamado 'appuser'
RUN adduser --disabled-password --no-create-home appuser

# Garante que o novo usuário tenha permissão para ler/escrever na pasta do projeto
RUN chown -R appuser:appuser /app

# Define que o container rodará com este usuário a partir de agora, não mais como root
USER appuser