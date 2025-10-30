import os
from dotenv import load_dotenv

# Wczytaj zmienne środowiskowe z pliku .env znajdującego się w głównym folderze projektu
load_dotenv()

class Config:
    """
    Główna klasa konfiguracyjny. Zbiera wszystkie ustawienia z jednego miejsca.
    
    AUDYT GOTOWOŚCI PRODUKCYJNEJ:
    - Zabezpieczenia: Wczytuje SECRET_KEY z .env
    - Logowanie: Ustawia DEBUG i LOG_TO_STDOUT (AUDYT 3.3)
    """
    
    # --- KRYTYCZNE USTAWIENIA BEZPIECZEŃSTWA ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("FATAL ERROR: Brak klucza SECRET_KEY! Ustaw go w pliku .env.")

    # --- USTAWIENIA BAZY DANYCH I FLASK ---
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///grafik.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- KONFIGURACJA LOGOWANIA (AUDYT 3.3) ---
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'
    TESTING = os.environ.get('FLASK_TESTING') == '1'
    # Włączenie logowania do konsoli (dobre dla kontenerów/Gunicorn)
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') == '1'
    
    # --- KONFIGURACJA SERWERA E-MAIL ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Grafik Firmowy', MAIL_USERNAME)

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("OSTRZEŻENIE: Brak konfiguracji MAIL_USERNAME lub MAIL_PASSWORD w .env. Wysyłka e-maili nie będzie działać.")

    # --- KONFIGURACJA REDIS QUEUE (RQ) ---
    # Używane do asynchronicznej wysyłki e-maili (AUDYT 2.2)
    RQ_REDIS_URL = os.environ.get('RQ_REDIS_URL', 'redis://localhost:6379/0')

    # --- USTAWIENIA DEWELOPERSKIE ---
    # Ustawione na 0 na produkcji (domyślnie, gdy DEBUG=False), ale dobre do dewelopmentu
    SEND_FILE_MAX_AGE_DEFAULT = 0
    TEMPLATES_AUTO_RELOAD = True
# --- NOWA KLASA TESTOWA (AUDYT 3.1) ---
# Dodaj tę klasę na dole pliku config.py

class TestConfig(Config):
    """Konfiguracja na potrzeby testów automatycznych."""

    # Ustawia Flaska w tryb testowy (zmienia zachowanie np. error handlerów)
    TESTING = True

    # Używamy czystej bazy danych SQLite w pamięci RAM.
    # To jest super-szybkie i gwarantuje, że każdy test jest czysty
    # i nie dotyka Twojej prawdziwej bazy 'grafik.db'.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Wyłączamy ochronę CSRF na potrzeby testów,
    # aby nie musieć generować tokenów w każdym teście POST.
    WTF_CSRF_ENABLED = False

    # Mówimy Flask-RQ2, aby wykonywał zadania synchronicznie (natychmiast).
    # Dzięki temu nie musimy uruchamiać serwera Redis ani workera RQ podczas testów.
    RQ_ASYNC = False

    # Wyłączamy logowanie do pliku podczas testów
    LOG_TO_STDOUT = None