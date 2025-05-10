# Base da imagem: Python 3 slim
FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia todos os arquivos do projeto para dentro do container
COPY . .

# Instala apenas as dependências Python necessárias
RUN pip install --no-cache-dir matplotlib networkx

# Comando default (substituído pelo docker-compose)
CMD ["python", "src/roteador.py"]
