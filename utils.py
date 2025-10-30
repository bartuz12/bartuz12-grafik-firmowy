import re
from flask import current_app, render_template
from datetime import datetime, timezone # Dodano timezone
# Importy dla e-maili (jeśli są tu)
# from threading import Thread
# from flask_mail import Message
# from extensions import mail, rq # Upewnij się, że importujesz poprawnie

def nl2br_filter(value):
    """Konwertuje znaki nowej linii na znaczniki <br>."""
    return value.replace('\n', '<br>\n')

def admin_or_manager_required(f):
    """Dekorator sprawdzający, czy użytkownik jest adminem lub kierownikiem."""
    from functools import wraps
    from flask_login import current_user
    from flask import abort
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.status not in ['admin', 'kierownik']:
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# --- POPRAWKA UTC ---
def inject_current_year():
    """Wstrzykuje aktualny rok (świadomy UTC) do kontekstu szablonu."""
    return {'current_year': datetime.now(timezone.utc).year}
# --- KONIEC POPRAWKI ---

# Funkcja do wysyłania e-maili (asynchroniczna lub synchroniczna w testach)
def send_email_in_background(recipients, subject, template, **context):
    """
    Wysyła e-mail w tle (używając RQ) lub synchronicznie (w trybie testowym).
    Akceptuje listę odbiorców lub pojedynczy adres.
    """
    from extensions import rq, mail # Import wewnątrz funkcji, aby uniknąć problemów
    from flask_mail import Message
    from flask import current_app # Potrzebne do kontekstu aplikacji

    # Upewnij się, że recipients jest listą
    if isinstance(recipients, str):
        recipients = [recipients]

    # Pobierz aktualną aplikację (ważne dla RQ i konfiguracji Mail)
    app = current_app._get_current_object()

    msg = Message(subject,
                  sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
                  recipients=recipients)
    msg.body = render_template(template + '.txt', **context)
    msg.html = render_template(template + '.html', **context)

    # Sprawdź, czy RQ ma działać asynchronicznie (z config.py)
    if app.config.get('RQ_ASYNC', True):
        # Działanie asynchroniczne (produkcja)
        try:
            # Używamy _send_email_task jako funkcji do zakolejkowania
            rq.get_queue().enqueue(_send_email_task, app.config, msg)
        except Exception as e:
            app.logger.error(f"Nie udało się zakolejkować e-maila do {recipients}: {e}")
            # Można rozważyć alternatywną metodę powiadomienia lub logowania
    else:
        # Działanie synchroniczne (testy)
        try:
            with app.app_context(): # Użyj kontekstu aplikacji
                 mail.send(msg)
        except Exception as e:
            app.logger.error(f"Błąd podczas synchronicznego wysyłania e-maila do {recipients}: {e}")


def _send_email_task(app_config, msg):
    """
    Funkcja pomocnicza wykonywana przez workera RQ.
    Potrzebuje konfiguracji aplikacji, aby móc ją odtworzyć.
    """
    # Ta funkcja działa w osobnym procesie workera RQ
    # Musimy odtworzyć kontekst aplikacji i instancję Mail
    from flask import Flask
    from extensions import mail # Importuj instancję mail
    from config import Config # Importuj swoją klasę Config

    # Stwórz tymczasową instancję aplikacji tylko do wysłania e-maila
    # Użyj konfiguracji przekazanej jako argument
    temp_app = Flask(__name__)
    # Zamiast ładować z obiektu, ładujemy z przekazanego słownika config
    # To wymaga dostosowania - przekazujemy cały app.config
    temp_app.config.from_mapping(app_config)

    # Zainicjuj mail z tymczasową aplikacją
    mail.init_app(temp_app)

    try:
        with temp_app.app_context():
            mail.send(msg)
            # Można dodać logowanie sukcesu, jeśli potrzebne
            # temp_app.logger.info(f"E-mail wysłany do {msg.recipients}")
    except Exception as e:
        # Logowanie błędów w kontekście workera
        # Użycie print, bo logger może nie być skonfigurowany w workerze
        print(f"Błąd workera RQ podczas wysyłania e-maila do {msg.recipients}: {e}")
# utils.py
import os
from flask import url_for, current_app
from datetime import datetime, timezone # Upewnij się, że masz ten import

# ... (twoje istniejące funkcje: nl2br_filter, admin_or_manager_required, inject_current_year, send_email_in_background, _send_email_task) ...

# --- NOWA FUNKCJA (AUDYT 3.2 - Cache Busting) ---
def url_for_static_bust(filename):
    """
    Generuje URL dla pliku statycznego z dodanym parametrem 'v'
    zawierającym timestamp ostatniej modyfikacji pliku.
    To zmusza przeglądarkę do pobrania nowej wersji tylko wtedy, gdy plik się zmienił.
    """
    filepath = os.path.join(current_app.static_folder, filename)
    if os.path.exists(filepath):
        timestamp = int(os.path.getmtime(filepath))
        return f"{url_for('static', filename=filename)}?v={timestamp}"
    # Zwróć standardowy URL, jeśli plik nie istnieje (np. błąd ścieżki)
    return url_for('static', filename=filename)
# --- KONIEC NOWEJ FUNKCJI ---