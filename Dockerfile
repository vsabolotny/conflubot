# Basis-Image mit Python
FROM python:3.10-slim-bullseye

# Arbeitsverzeichnis setzen
WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY . .

# Standardbefehl zum Ausführen (kannst du anpassen)
CMD ["python", "main.py"]