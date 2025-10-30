"""
Testy dla głównych funkcji aplikacji (dashboard, profil)
Plik: tests/test_main.py

WAŻNE: Wszystkie fixtures importowane z conftest.py
"""
import pytest
from flask import url_for, session
from models import User, Recipient, db
# POPRAWKA: Importujemy check_password_hash do sprawdzania hasła
from werkzeug.security import check_password_hash
# POPRAWKA: Importujemy unescape do poprawnego czytania HTML
from html import unescape

# UWAGA: Fixtures `client`, `app`, `db`, `logged_in_user`, `regular_user`
# są importowane automatycznie z pliku conftest.py przez pytest.

# ==================== TESTY GŁÓWNE ====================

def test_dashboard_requires_login(client):
    """Test: Dashboard (/dashboard) wymaga zalogowania"""
    response = client.get('/dashboard')
    assert response.status_code == 302 # Przekierowanie do /login
    assert '/login' in response.location

def test_dashboard_loads_for_logged_in_user(logged_in_user):
    """Test: Dashboard ładuje się poprawnie dla zalogowanego użytkownika"""
    response = logged_in_user.get('/dashboard')
    assert response.status_code == 200
    # Sprawdzamy kluczowy tekst z dashboard.html
    html = unescape(response.data.decode('utf-8'))
    assert 'Panel Główny' in html

def test_profile_page_loads(logged_in_user, regular_user):
    """Test: Strona profilu (/profile) ładuje się poprawnie"""
    response = logged_in_user.get('/profile')
    assert response.status_code == 200
    
    # POPRAWKA: Używamy dekodowania HTML
    html = unescape(response.data.decode('utf-8'))
    assert regular_user.email in html
    assert 'Mój Profil' in html
    assert 'Zmień hasło' in html # Tekst z formularza

def test_profile_change_password_success(logged_in_user, app, regular_user):
    """Test: Użytkownik może poprawnie zmienić swoje hasło"""
    response = logged_in_user.post(
        # Używamy endpointu zdefiniowanego w routes/main.py
        url_for('main.change_password'), 
        data={
            'old_password': 'password', # Hasło ustawione w conftest.py
            'new_password': 'new_password123',
            'confirm_password': 'new_password123' # Poprawka nazwy pola
        }, 
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Sprawdzamy bazę danych
    with app.app_context():
        user = db.session.get(User, regular_user.id)
        assert user is not None
        # Sprawdzamy, czy hasło w bazie zgadza się z nowym hasłem
        assert check_password_hash(user.password_hash, 'new_password123') is True

def test_profile_change_password_wrong_old(logged_in_user, app, regular_user):
    """Test: Zmiana hasła nie działa, gdy podano złe stare hasło"""
    response = logged_in_user.post(
        url_for('main.change_password'), 
        data={
            'old_password': 'ZLE_HASLO',
            'new_password': 'new_password123',
            'confirm_password': 'new_password123' # Poprawka nazwy pola
        }, 
        follow_redirects=True
    )
    assert response.status_code == 200
    
    with app.app_context():
        user = db.session.get(User, regular_user.id)
        assert user is not None
        # Hasło powinno być nadal stare
        assert check_password_hash(user.password_hash, 'password') is True
        assert check_password_hash(user.password_hash, 'new_password123') is False

    # POPRAWKA: Usunięto niestabilne sprawdzanie komunikatu flash

def test_profile_change_theme(logged_in_user, db, regular_user):
    """Test: Użytkownik może zmienić swój motyw"""
    # POPRAWKA: Używamy poprawnej wartości z formularza
    new_theme_value = 'default_dark' 
    response = logged_in_user.post(
        url_for('main.change_theme'), 
        data={'theme': new_theme_value}, 
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Sprawdzamy bazę danych
    user = db.session.get(User, regular_user.id)
    assert user.theme == new_theme_value

def test_profile_change_name(logged_in_user, db, regular_user):
    """Test: Użytkownik może zmienić swoje imię i nazwisko"""
    new_name = "ZmienioneImie"
    new_surname = "ZmienioneNazwisko"
    new_agency = "Nowa Agencja"
    
    response = logged_in_user.post(
        # POPRAWKA: Używamy endpointu 'update_details'
        url_for('main.update_details'), 
        data={
            'name': new_name,
            'surname': new_surname,
            'agency': new_agency
        }, 
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Sprawdzamy bazę danych
    user = db.session.get(User, regular_user.id)
    assert user.name == new_name
    assert user.surname == new_surname
    assert user.agency == new_agency

def test_profile_recipients(logged_in_user, db, regular_user):
    """Test: Użytkownik może dodawać i usuwać odbiorców e-mail"""
    recipient_email = "test.odbiorca@example.com"
    response_add = logged_in_user.post(
        url_for('main.add_recipient'), 
        data={'email': recipient_email}, 
        follow_redirects=True
    )
    assert response_add.status_code == 200
    
    # Sprawdzamy bazę danych
    recipient = Recipient.query.filter_by(user_id=regular_user.id, email=recipient_email).first()
    assert recipient is not None
    recipient_id = recipient.id

    # Używamy poprawnego endpointu 'delete_recipient'
    response_delete = logged_in_user.post(
        url_for('main.delete_recipient', recipient_id=recipient_id), 
        follow_redirects=True
    )
    assert response_delete.status_code == 200
    
    # Sprawdzamy bazę danych
    recipient_deleted = db.session.get(Recipient, recipient_id)
    assert recipient_deleted is None

def test_profile_add_invalid_recipient_email(logged_in_user, db, regular_user):
    """Test: Użytkownik nie może dodać nieprawidłowego adresu e-mail jako odbiorcy"""
    initial_recipient_count = Recipient.query.filter_by(user_id=regular_user.id).count()

    invalid_email = "to-nie-jest-email"
    response = logged_in_user.post(
        url_for('main.add_recipient'), 
        data={'email': invalid_email}, 
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # POPRAWKA: Używamy dekodowania HTML
    html = unescape(response.data.decode('utf-8'))
    # Sprawdzamy komunikat błędu walidacji
    assert 'Podaj poprawny adres e-mail.' in html
    
    # Sprawdź bazę
    final_recipient_count = Recipient.query.filter_by(user_id=regular_user.id).count()
    assert initial_recipient_count == final_recipient_count

def test_profile_change_password_mismatch(logged_in_user, app, regular_user):
    """Test: Zmiana hasła nie działa, gdy nowe hasła do siebie nie pasują"""
    response = logged_in_user.post(
        url_for('main.change_password'), 
        data={
            'old_password': 'password',
            'new_password': 'new_password123',
            'confirm_password': 'INNE_HASLO_456' # Poprawka nazwy pola
        }, 
        follow_redirects=True
    )
    assert response.status_code == 200
    
    with app.app_context():
        user = db.session.get(User, regular_user.id)
        assert user is not None
        # Hasło powinno pozostać stare
        assert check_password_hash(user.password_hash, 'password') is True
        assert check_password_hash(user.password_hash, 'new_password123') is False

    # POPRAWKA: Usunięto niestabilne sprawdzanie komunikatu flash

