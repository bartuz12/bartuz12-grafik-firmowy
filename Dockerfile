# Używamy oficjalnego, lekkiego obrazu Pythona
FROM python:3.11-slim

# --- KRYTYCZNA POPRAWKA DLA "Build failed" ---
# Instalujemy narzędzia systemowe (build-essential) potrzebne do kompilacji np. "pandas"
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*
# --- KONIEC POPRAWKI ---

# Ustawiamy katalog roboczy wewnątrz kontenera
WORKDIR /app

# Ustawiamy zmienną środowiskową, której oczekuje Cloud Run
ENV PORT=8080

# Kopiujemy listę zależności i instalujemy je
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy cały kod projektu
COPY . .

# Polecenie uruchamiające serwer Gunicorn
# ✅ OSTATECZNA POPRAWKA — usunięto "\" przed $PORT
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 aplikacja:create_app
