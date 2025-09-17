FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Abhängigkeiten installieren
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
