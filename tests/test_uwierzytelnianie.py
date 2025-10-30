"""
Testy dla funkcji uwierzytelniania
Plik: tests/test_uwierzytelnianie.py

WAŻNE: Wszystkie fixtures importowane z conftest.py
"""
import pytest
from flask import session, url_for
from models import User, db # Upewnij się, że db jest importowane

# UWAGA: Fixtures `client`, `app`
# są importowane automatycznie z pliku conftest.py przez pytest.

# === POPRAWKA: Usunięto 'db' z argumentów ===
def test_registration_flow(client, app): # 'app' jest potrzebne dla app_context
    """
    Test A-1: Sprawdza pełny proces rejestracji (POST)
    i weryfikuje, czy użytkownik został dodany do bazy danych.
    """
    # === KROK 1: Wyślij żądanie POST rejestracji (BEZ follow_redirects) ===
    response_post = client.post('/register', data={
        'name': 'Test',
        'surname': 'UserReg',
        'email': 'test_reg@example.com',
        'agency': 'DPL',
        'password': 'password123',
        'confirm_password': 'password123',
        'accept_tos': 'True'
    }) # Usunięto follow_redirects=True

    # === KROK 2: Sprawdź, czy odpowiedź to przekierowanie (302 Found) na stronę logowania ===
    # W środowisku testowym BEZ działającego Redisa (RQ_ASYNC=False),
    # próba zakolejkowania powinna być synchroniczna i nie powodować błędu.
    # Jeśli jednak powoduje (co widzieliśmy), kod auth.py łapie błąd i NADAL przekierowuje.
    assert response_post.status_code == 302, f"Oczekiwano przekierowania (302), otrzymano {response_post.status_code}."
    assert response_post.location == '/login', f"Oczekiwano przekierowania na /login, otrzymano {response_post.location}"

    # === KROK 3: Wykonaj żądanie GET do strony, na którą nastąpiło przekierowanie ===
    response_get_login = client.get(response_post.location)
    assert response_get_login.status_code == 200

    # === KROK 4: Sprawdź komunikat flash ===
    # Sprawdzamy oba możliwe komunikaty (sukces lub ostrzeżenie o Redis)
    response_data_str = response_get_login.data.decode('utf-8')
    success_msg = 'Rejestracja pomyślna! Możesz się teraz zalogować.'
    warning_msg = 'Rejestracja pomyślna, ale wystąpił problem z wysyłką e-maila powitalnego.'
    assert success_msg in response_data_str or warning_msg in response_data_str

    # === KROK 5: Sprawdź, czy użytkownik FAKTYCZNIE jest w bazie ===
    with app.app_context(): # Użyj kontekstu aplikacji do zapytania
        user = User.query.filter_by(email='test_reg@example.com').first()
        assert user is not None
        assert user.name == 'Test'