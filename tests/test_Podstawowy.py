# Ten plik sprawdza podstawowe, anonimowe funkcje aplikacji

def test_login_page_loads(client):
    """
    Test G-1: Sprawdza, czy strona logowania (GET) ładuje się poprawnie.
    'client' to fixture zdefiniowany w conftest.py.
    """
    response = client.get('/login')
    
    # Sprawdź, czy serwer odpowiedział kodem 200 (OK)
    assert response.status_code == 200
    
    # Sprawdź, czy w treści strony znajduje się tekst "Zaloguj się"
    # Używamy b'' dla stringów binarnych (bytes)
    # Używamy kodowania utf-8 dla polskich znaków
    assert 'Zaloguj się' in response.data.decode('utf-8')

def test_unauthenticated_access_to_admin(client):
    """
    Test G-2: Sprawdza, czy niezalogowany użytkownik jest przekierowywany
    z chronionej strony /admin/users na stronę logowania.
    """
    # follow_redirects=True sprawia, że klient podąża za przekierowaniem
    response = client.get('/admin/users', follow_redirects=True)
    
    # Sprawdź, czy strona się załadowała
    assert response.status_code == 200
    
    # Sprawdź, czy zostaliśmy przekierowani na stronę logowania
    # i czy pojawił się komunikat flash od Flask-Login
    assert 'Proszę się zalogować' in response.data.decode('utf-8')
