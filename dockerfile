FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Dependencies installieren (für cryptography & python-kasa wichtig!)
RUN apt-get update && apt-get install -y \
    libffi-dev \
    libssl-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY . .

# Uploads-Verzeichnis vorbereiten
RUN mkdir -p uploads

# Flask läuft standardmäßig auf Port 5000
EXPOSE 5000

# Startbefehl
CMD ["python", "app.py"]
