FROM python:3.10

WORKDIR /app

# Copie o arquivo requirements.txt para o diretório de trabalho
COPY requirements.txt .

# Instale as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copie todos os arquivos do projeto para o diretório de trabalho do contêiner
COPY . .

# Exponha a porta que a aplicação irá rodar (ajuste conforme necessário)
EXPOSE 3000

# Defina o comando para iniciar a aplicação
CMD ["python", "main.py"]
