Używamy oficjalnego, lekkiego obrazu Pythona

FROM python:3.11-slim

Ustawiamy katalog roboczy wewnątrz kontenera

WORKDIR /app

Ustawiamy zmienną środowiskową, której oczekuje Cloud Run

ENV PORT 8080

Kopiujemy tylko listę zależności i ją instalujemy

To przyspiesza budowanie, jeśli kod się zmienia, a zależności nie

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

Kopiujemy cały kod projektu (aplikacja.py, trasy/, szablony/ itd.)

COPY . .

Polecenie uruchamiające serwer Gunicorn

Używamy nazwy Twojego pliku 'aplikacja.py' i funkcji 'create_app'

Poprawka: 'aplikacja:create_app' zamiast 'app:create_app()'

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 aplikacja:create_app