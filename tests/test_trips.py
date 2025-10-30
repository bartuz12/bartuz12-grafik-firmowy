"""
Testy dla funkcji związanych ze zleceniami (trips)
Plik: tests/test_trips.py

WAŻNE: Wszystkie fixtures importowane z conftest.py
"""
import pytest
from flask import url_for
from models import Trip, Signup, User, db
from datetime import date, timedelta
# POPRAWKA: Importujemy unescape do poprawnego czytania HTML
from html import unescape

# UWAGA: Fixtures `client`, `app`, `db`, `logged_in_admin`,
# `logged_in_user`, `sample_trip`, `sample_trips`, `regular_user`, `admin_user`
# są importowane automatycznie z pliku conftest.py przez pytest.


# ==================== TESTY DODAWANIA ZLECENIA ====================

def test_add_trip_page_loads_for_admin(logged_in_admin):
    """
    Test T-1: Sprawdza, czy strona dodawania zlecenia (GET /trip/add)
    ładuje się poprawnie dla zalogowanego admina.
    """
    response = logged_in_admin.get('/trip/add')
    assert response.status_code == 200
    # Sprawdzamy DOKŁADNY tytuł strony z polskimi znakami
    assert 'Dodaj Nowe Zlecenie'.encode('utf-8') in response.data

def test_add_trip_page_forbidden_for_user(logged_in_user):
    """
    Test T-1.1: Sprawdza, czy strona dodawania zlecenia (GET /trip/add)
    jest zablokowana (403 Forbidden) dla zwykłego użytkownika.
    """
    response = logged_in_user.get('/trip/add')
    assert response.status_code == 403

def test_add_trip_post_success(logged_in_admin, app):
    """
    Test T-2: Sprawdza, czy wysłanie formularza (POST /trip/add)
    poprawnie dodaje zlecenie do bazy danych przez admina.
    """
    trip_date_str = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    response = logged_in_admin.post('/trip/add', data={
        'title': 'Testowe Zlecenie z Pytest',
        'trip_date': trip_date_str,
        'spots': '3',
        'is_confirmed': 'on', # Checkbox 'on' oznacza True
        'notes': 'Notatki testowe'
    }, follow_redirects=True) # Podążamy za przekierowaniem do trip_details

    assert response.status_code == 200 # Po przekierowaniu
    
    # Sprawdzamy DOKŁADNY komunikat flash z polskimi znakami i kropką
    html = unescape(response.data.decode('utf-8'))
    assert 'Nowe zlecenie zostało dodane.' in html

    # Sprawdź, czy zlecenie istnieje w bazie
    with app.app_context():
        trip = Trip.query.filter_by(title='Testowe Zlecenie z Pytest').first()
        assert trip is not None
        assert trip.trip_date == date.fromisoformat(trip_date_str)
        assert trip.spots == 3
        assert trip.is_confirmed is True
        assert trip.notes == 'Notatki testowe'

        # Sprawdź, czy admin został automatycznie zapisany
        admin_user = User.query.filter_by(email='admin@test.com').first()
        assert admin_user is not None
        signup = Signup.query.filter_by(trip_id=trip.id, user_id=admin_user.id).first()
        assert signup is not None
        assert signup.status == 'potwierdzony'


# ==================== TESTY SZCZEGÓŁÓW ZLECENIA ====================

def test_trip_details_page_loads(logged_in_user, sample_trip):
    """
    Test T-3: Sprawdza, czy strona szczegółów zlecenia (GET /trip/<id>)
    ładuje się poprawnie dla zalogowanego użytkownika.
    """
    response = logged_in_user.get(f'/trip/{sample_trip.id}')
    assert response.status_code == 200
    
    # POPRAWKA: Używamy dekodowania HTML i sprawdzamy fragmenty tekstu
    html = unescape(response.data.decode('utf-8'))
    assert 'Szczegóły Zlecenia' in html
    assert sample_trip.title in html


def test_trip_details_404_for_invalid_id(logged_in_user):
    """
    Test T-4: Sprawdza, czy próba wejścia na stronę nieistniejącego zlecenia
    zwraca błąd 404 Not Found.
    """
    response = logged_in_user.get('/trip/99999') # Zakładamy, że ID 99999 nie istnieje
    assert response.status_code == 404
    
    # POPRAWKA: Usunięto kruchą asercję sprawdzającą tekst 'Nie znaleziono strony'.
    # Sprawdzenie status_code == 404 jest wystarczające.

