"""
Plik konfiguracyjny Pytest (conftest.py)
Zawiera fixtures (narzędzia) wielokrotnego użytku dla wszystkich testów.
"""
import pytest
# Usunięto 'import warnings', ponieważ filtry są teraz w pytest.ini
from datetime import date, timedelta, time
from app import create_app
from config import Config
# Importujemy 'db' z extensions, aby uniknąć cyklicznego importu z app
from extensions import db as _db 
# Importujemy modele potrzebne do stworzenia fixtures
from models import User, Trip, Signup
# Usunięto 'from sqlalchemy.exc import LegacyAPIWarning'

# === Usunięto sekcję warnings.filterwarnings() ===

# --- 1. KONFIGURACJA APLIKACJI I BAZY DANYCH ---

class TestConfig(Config):
    """Konfiguracja testowa - używa bazy w pamięci (SQLite)"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Używa bazy w pamięci RAM
    WTF_CSRF_ENABLED = False # Wyłącza tokeny CSRF na czas testów formularzy
    SECRET_KEY = 'test-secret-key' # Klucz testowy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RQ_ASYNC = False # Wyłącza Redis, zadania wykonują się synchronicznie

@pytest.fixture(scope='session')
def app():
    """
    Fixture na poziomie sesji: Tworzy i konfiguruje nową instancję aplikacji
    Flask dla całej sesji testowej. Używa konfiguracji TestConfig.
    """
    app = create_app(config_class=TestConfig)
    
    # Ustawienie kontekstu aplikacji jest ważne dla operacji
    # wymagających dostępu do `current_app` (np. db.create_all()).
    with app.app_context():
        yield app

@pytest.fixture(scope='function')
def db(app):
    """
    Fixture na poziomie funkcji: Tworzy nową, czystą bazę danych
    dla każdego pojedynczego testu.
    """
    # Upewnij się, że jesteśmy w kontekście aplikacji
    with app.app_context():
        _db.create_all() # Tworzy wszystkie tabele
        yield _db # Udostępnia 'db' testowi
        
        # Czystka po teście
        _db.session.remove()
        _db.drop_all() # Usuwa wszystkie tabele

@pytest.fixture(scope='function')
def client(app, db):
    """
    Fixture na poziomie funkcji: Udostępnia klienta testowego Flaska
    dla każdego testu, z czystą bazą danych (dzięki zależności od 'db').
    """
    return app.test_client()

# --- 2. FIXTURES TWORZĄCE DANE (UŻYTKOWNICY I ZLECENIA) ---
# Używamy scope='function', aby dane były świeże dla każdego testu

@pytest.fixture(scope='function')
def admin_user(db): # Zależy od 'db', aby baza istniała
    """Tworzy i zwraca testowego użytkownika 'admin'"""
    admin = User(
        name='Admin',
        surname='Testowy',
        email='admin@test.com',
        agency='TEST',
        status='admin',
        accepted_tos=True
    )
    admin.set_password('password')
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture(scope='function')
def regular_user(db):
    """Tworzy i zwraca testowego użytkownika 'pracownik'"""
    user = User(
        name='Jan',
        surname='Kowalski',
        email='user@test.com',
        agency='TEST',
        status='pracownik',
        accepted_tos=True
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def kierownik_user(db):
    """Tworzy i zwraca testowego użytkownika 'kierownik'"""
    kierownik = User(
        name='Anna',
        surname='Zarządca',
        email='kierownik@test.com',
        agency='TEST',
        status='kierownik',
        accepted_tos=True
    )
    kierownik.set_password('password')
    db.session.add(kierownik)
    db.session.commit()
    return kierownik

@pytest.fixture(scope='function')
def sample_trip(db):
    """Tworzy i zwraca jedno przykładowe zlecenie."""
    trip = Trip(
        title='Wyjazd Testowy Pojedynczy',
        trip_date=date.today() + timedelta(days=10),
        spots=5,
        is_confirmed=True
    )
    db.session.add(trip)
    db.session.commit()
    return trip

@pytest.fixture(scope='function')
def sample_trips(db):
    """Tworzy i zwraca listę kilku przykładowych zleceń."""
    trip1 = Trip(title='Wyjazd Testowy A', trip_date=date(2025, 11, 10), spots=2, is_archived=False)
    trip2 = Trip(title='Wyjazd Testowy B', trip_date=date(2025, 11, 15), spots=4, is_archived=False)
    
    # Dodajemy listę, aby upewnić się, że test `clear_month` ma co usunąć
    trips = [trip1, trip2]
    db.session.add_all(trips)
    db.session.commit()
    return trips

# --- 3. FIXTURES DO LOGOWANIA (UŻYWANE W TESTACH) ---

def _login(client, email, password):
    """Wewnętrzna funkcja pomocnicza do logowania"""
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

@pytest.fixture(scope='function')
def logged_in_admin(client, admin_user):
    """Loguje admina i zwraca klienta."""
    _login(client, admin_user.email, 'password')
    yield client
    client.get('/logout', follow_redirects=True) # Wyloguj po teście

@pytest.fixture(scope='function')
def logged_in_kierownik(client, kierownik_user):
    """Loguje kierownika i zwraca klienta."""
    _login(client, kierownik_user.email, 'password')
    yield client
    client.get('/logout', follow_redirects=True)

@pytest.fixture(scope='function')
def logged_in_user(client, regular_user):
    """Loguje zwykłego użytkownika i zwraca klienta."""
    _login(client, regular_user.email, 'password')
    yield client
    client.get('/logout', follow_redirects=True)

# --- 4. FILTRY OSTRZEŻEŃ ---
# (Usunięto fixture 'suppress_warnings', ponieważ filtry są teraz w pytest.ini)

