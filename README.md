Grafik Firmowy (Aplikacja Webowa)

1. Opis Projektu

Aplikacja "Grafik Firmowy" to zaawansowane narzędzie webowe typu "single-page application" (SPA) do zarządzania zleceniami i personelem. Została zbudowana w oparciu o framework Flask (Python) po stronie serwera oraz dynamiczny JavaScript (Vanilla JS) po stronie klienta.

Aplikacja umożliwia administratorom i kierownikom pełne zarządzanie grafikiem zleceń, podczas gdy pracownicy (w tym "złoci pracownicy") mogą przeglądać zlecenia i zarządzać swoimi zapisami.

2. Główne Funkcjonalności

System Uwierzytelniania: Pełna obsługa rejestracji, logowania, wylogowywania i resetowania hasła (z tokenem e-mail).

System Ról Użytkowników:

Administrator/Kierownik: Pełny dostęp do edycji, dodawania, usuwania i zarządzania zleceniami oraz użytkownikami.

Pracownik: Może przeglądać zlecenia i zapisywać się na nie.

Złoty Pracownik: Jest automatycznie "wstępnie zapisywany" na każde nowo utworzone zlecenie i musi jedynie potwierdzić swój udział.

Interaktywny Kalendarz: (FullCalendar) z widokiem miesiąca, tygodnia i listy.

Dynamiczna Edycja:

Widok Siatki (Miesiąc/Tydzień): Edycja zleceń odbywa się w oknie modalnym (pop-up) bez przeładowywania strony.

Widok Listy: Umożliwia administratorom szybki podgląd szczegółów (godziny, kilometry) poprzez rozwinięcie panelu.

Panel Administracyjny:

Zarządzanie użytkownikami (zmiana statusu, agencji).

Archiwizacja starych zleceń.

Import zleceń z plików Excel.

Eksport grafiku do pliku Excel (dla agencji DPL).

Zbiorcza Edycja Zleceń: (Strona "Rozliczenia") Dedykowana strona dla admina do masowej edycji zleceń, inteligentnie podzielona na "Zlecenia Przyszłe" (planowanie) i "Zlecenia Przeszłe" (rozliczanie).

Personalizacja: Użytkownicy mogą zmieniać motyw kolorystyczny aplikacji (domyślny, ciemny, leśny lub własny kolor).

Powiadomienia E-mail: Automatyczne wysyłanie wiadomości po rejestracji, przy resecie hasła, czy wysyłaniu listy do biura.

PWA (Progressive Web App): Aplikacja posiada manifest.json i service-worker.js, co umożliwia jej "instalację" na urządzeniach mobilnych i zapewnia podstawową funkcjonalność offline.

3. Struktura Technologiczna

Backend: Python 3.x z frameworkiem Flask.

Baza Danych: SQLAlchemy (domyślnie skonfigurowana do użycia SQLite - grafik.db).

Frontend: HTML5, CSS3 (z zmiennymi CSS dla motywów), Vanilla JavaScript (ES6+).

Główne Biblioteki:

FullCalendar.js (dla kalendarza)

Pandas (do obsługi importu/eksportu plików Excel)

Architektura: Aplikacja jest zbudowana w oparciu o wzorzec Application Factory (create_app) i moduły Flask Blueprints (w folderze /routes), co zapewnia wysoką skalowalność i czytelność kodu.

4. Struktura Plików

/grafik-firmowy/
|-- app.py             # Główna fabryka aplikacji (tworzy i łączy moduły)
|-- config.py          # Klasa konfiguracyjna (wczytuje dane z .env)
|-- models.py          # Modele bazy danych (SQLAlchemy)
|-- utils.py           # Funkcje pomocnicze (np. wysyłka e-mail, dekoratory)
|-- requirements.txt   # Zależności projektu (pip install -r requirements.txt)
|-- .env               # Plik z sekretami (klucze API, hasła - NIEUDOSTĘPNIAĆ)
|
|-- /routes/           # Moduły (Blueprints) z logiką aplikacji
|   |-- __init__.py    # Pusty plik oznaczający pakiet
|   |-- auth.py        # Logika logowania, rejestracji, resetu hasła
|   |-- main.py        # Logika dashboardu, profilu i głównych API
|   |-- trips.py       # Logika dodawania, edycji i zapisów na zlecenia
|   `-- admin.py       # Logika panelu admina (zarządzanie, import, rozliczenia)
|
|-- /static/           # Pliki statyczne (CSS, JS, PWA)
|   |-- /css/
|   |   |-- style.css        # Główny arkusz stylów (layout, menu, karty)
|   |   `-- dashboard.css    # Style specyficzne dla kalendarza
|   |-- /js/
|   |   |-- dashboard_main.js      # Główna logika kalendarza i modali
|   |   `-- dashboard_list_edit.js # Logika widoku listy (rozwijanie)
|   |-- manifest.json
|   `-- service-worker.js
|
`-- /templates/        # Szablony HTML (Jinja2)
    |-- layout.html    # Główny szablon (master page) z nawigacją
    |-- dashboard.html # Panel główny z kalendarzem
    |-- admin_settlements.html # Strona zbiorczej edycji
    |-- trip_details.html      # Strona szczegółów zlecenia
    |-- _trip_details_fragment.html # Fragment ładowany do modala
    |-- (pozostałe szablony: login.html, profile.html, admin_users.html, etc.)
    |
    `-- /email/        # Szablony e-maili tekstowych
        |-- welcome.txt
        |-- new_trip.txt
        |-- reset_password.txt
        `-- (itp.)


5. Instrukcja Uruchomienia

Zainstaluj zależności:

pip install -r requirements.txt


Stwórz plik .env: W głównym folderze projektu stwórz plik o nazwie .env.

Uzupełnij plik .env: Skopiuj do niego zawartość z pliku env.example (lub przepisz ręcznie) i uzupełnij swoje dane:

SECRET_KEY='TWÓJ_SUPER_TAJNY_KLUCZ'
MAIL_SERVER='smtp.gmail.com'
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME='TWÓJ_EMAIL@gmail.com'
MAIL_PASSWORD='TWOJE_HASŁO_DO_APLIKACJI_GOOGLE'


Uruchom aplikację:

python app.py