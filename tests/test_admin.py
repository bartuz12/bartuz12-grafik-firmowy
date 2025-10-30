"""
Testy funkcji administracyjnych
Plik: tests/test_admin.py

WAŻNE: Wszystkie fixtures importowane z conftest.py
"""
import pytest
from flask import url_for
from models import User, Trip, db
from datetime import date, timedelta

# UWAGA: Fixtures `client`, `app`, `logged_in_admin`, `logged_in_user`, `logged_in_kierownik`,
# `regular_user`, `admin_user`, `kierownik_user`, `sample_trips`, `sample_trip`
# są teraz importowane automatycznie z pliku conftest.py przez pytest.

# ==================== TESTY DOSTĘPU ====================

def test_admin_panel_requires_login(client):
    """Admin panel /admin/users wymaga zalogowania"""
    response = client.get('/admin/users')
    assert response.status_code == 302
    assert '/login' in response.location

def test_regular_user_cannot_access_admin(logged_in_user):
    """Zwykły użytkownik nie ma dostępu do panelu admina (/admin/users -> 403)"""
    response = logged_in_user.get('/admin/users')
    # Oczekujemy 403 Forbidden, bo użytkownik jest zalogowany, ale nie ma uprawnień
    assert response.status_code == 403

def test_admin_can_access_admin_panel(logged_in_admin, admin_user):
    """Administrator ma dostęp do panelu /admin/users"""
    response = logged_in_admin.get('/admin/users')
    assert response.status_code == 200
    # Poprawka: Szukamy e-maila admina, który na pewno tam jest
    assert admin_user.email.encode('utf-8') in response.data
    # Poprawka: Szukamy tekstu, który na pewno jest w szablonie (np. nagłówek tabeli)
    assert b'<th>Email</th>' in response.data

def test_kierownik_can_access_admin_panel(logged_in_kierownik, kierownik_user):
    """Kierownik ma dostęp do panelu /admin/users (zgodnie z @admin_or_manager_required)"""
    response = logged_in_kierownik.get('/admin/users')
    assert response.status_code == 200
    # Poprawka: Szukamy e-maila kierownika, który na pewno tam jest
    assert kierownik_user.email.encode('utf-8') in response.data
    assert b'<th>Email</th>' in response.data

# ==================== TESTY ZARZĄDZANIA UŻYTKOWNIKAMI ====================

def test_admin_can_view_users_list(logged_in_admin, regular_user):
    """Admin widzi listę użytkowników, w tym regular_user"""
    response = logged_in_admin.get('/admin/users')
    assert response.status_code == 200
    assert regular_user.email.encode('utf-8') in response.data

def test_change_user_status(logged_in_admin, app, regular_user):
    """Admin może zmienić status użytkownika"""
    user_id_to_change = regular_user.id
    response = logged_in_admin.post(
        f'/admin/users/set-status/{user_id_to_change}',
        data={'status': 'kierownik'},
        follow_redirects=True
    )
    assert response.status_code == 200
    # Sprawdź DOKŁADNY tekst komunikatu flash z routes/admin.py (zakodowany)
    expected_flash = f'Zmieniono status dla {regular_user.name} {regular_user.surname}.'
    assert expected_flash.encode('utf-8') in response.data

    user = db.session.get(User, user_id_to_change)
    assert user is not None
    assert user.status == 'kierownik'

def test_cannot_set_invalid_status(logged_in_admin, regular_user):
    """Nie można ustawić nieprawidłowego statusu użytkownika"""
    user_id_to_change = regular_user.id
    response = logged_in_admin.post(
        f'/admin/users/set-status/{user_id_to_change}',
        data={'status': 'nieprawidlowy_status'},
        follow_redirects=True
    )
    assert response.status_code == 200
    # Sprawdź DOKŁADNY tekst komunikatu flash z routes/admin.py (zakodowany)
    assert 'Wybrano nieprawidłowy status.'.encode('utf-8') in response.data

# ==================== TESTY ZARZĄDZANIA ZLECENIAMI (w panelu admina) ====================

def test_admin_can_view_settlements(logged_in_admin, sample_trips):
    """Admin widzi stronę rozliczeń i tytuł zlecenia z fixture"""
    response = logged_in_admin.get('/admin/settlements')
    assert response.status_code == 200
    assert len(sample_trips) > 0
    # Poprawka: Sprawdzamy, czy tytuł strony "Rozliczenia" jest obecny
    assert 'Rozliczenia'.encode('utf-8') in response.data
    # POPRAWKA: Usunięto asercję sprawdzającą e-mail admina (admin@test.com),
    # ponieważ szablon 'admin/settlements.html' go nie wyświetla.
    # Ten test teraz sprawdza tylko, czy strona się ładuje i ma poprawny tytuł.


def test_admin_can_archive_trip(logged_in_admin, app, sample_trip):
    """Admin może archiwizować zlecenia przez POST na /admin/archive/run"""
    trip_id_to_check = sample_trip.id
    
    trip = db.session.get(Trip, trip_id_to_check)
    if trip:
        trip.trip_date = date.today() - timedelta(days=200) # Ustaw datę w przeszłości
        db.session.commit()
    else:
        pytest.skip("Sample trip not found in DB for archiving test")

    response = logged_in_admin.post('/admin/archive/run', follow_redirects=True)
    assert response.status_code == 200
    # Poprawka: Szukamy DOKŁADNEGO tekstu flash z polskimi znakami
    assert 'Pomyślnie zarchiwizowano'.encode('utf-8') in response.data

    trip = db.session.get(Trip, trip_id_to_check)
    assert trip is not None
    assert trip.is_archived is True

def test_clear_month(logged_in_admin, app, sample_trips):
    """Admin może wyczyścić miesiąc przez POST na /admin/clear-month (AJAX)"""
    # Upewnij się, że sample_trips stworzyły zlecenia w listopadzie 2025
    initial_count = Trip.query.filter(
        db.extract('year', Trip.trip_date) == 2025,
        db.extract('month', Trip.trip_date) == 11,
        Trip.is_archived == False
    ).count()
    nov_trip_exists = any(t.trip_date.year == 2025 and t.trip_date.month == 11 for t in sample_trips if t and t.id is not None)
    if not nov_trip_exists or initial_count == 0:
         pytest.skip("Fixture sample_trips did not create trips in Nov 2025 for clear_month test")

    response = logged_in_admin.post('/admin/clear-month', json={'year': 2025, 'month': 11})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    # Poprawka: DOKŁADNY tekst komunikatu
    expected_message = f'Pomyślnie usunięto {initial_count} zleceń z 11/2025.'
    assert expected_message == data.get('message')

# ==================== TEST WALIDACJI (Usunięto database_isolation) ====================

def test_db_fixture_works(db):
    """Sprawdza, czy fixture db poprawnie tworzy i usuwa tabele"""
    user = User(email='dbtest@example.com', name='DB', surname='Test', agency='Test')
    user.set_password('test')
    db.session.add(user)
    db.session.commit()
    found = User.query.filter_by(email='dbtest@example.com').first()
    assert found is not None

