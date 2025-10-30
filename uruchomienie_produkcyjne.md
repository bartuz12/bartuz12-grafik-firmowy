Instrukcje Uruchomienia Aplikacji z RQ (Redis Queue)

Aby aplikacja działała poprawnie (zwłaszcza wysyłka e-maili), musisz mieć uruchomione TRZY komponenty:

Serwer Redis: Baza danych dla kolejki zadań.

Aplikacja Flask: Twój główny serwer webowy.

Worker RQ: Proces w tle, który wykonuje zadania z kolejki.

Krok 1: Uruchom Serwer Redis

Upewnij się, że masz zainstalowany i uruchomiony serwer Redis. Domyślnie nasłuchuje on na porcie 6379. Jeśli używasz Windowsa, możesz pobrać go stąd lub użyć WSL.

Krok 2: Uruchom Głównego Workera RQ

Otwórz pierwszy terminal w folderze projektu (grafik-firmowy) i uruchom workera:

# Ustawienie zmiennej, aby wskazać na Twój główny plik
set FLASK_APP=app.py

# Uruchomienie workera (będzie nasłuchiwał na zadania)
flask rq worker


Ten terminal musi pozostać otwarty. Będziesz w nim widział logi, gdy e-maile są wysyłane (np. "E-mail (w tle) wysłany pomyślnie...").

Krok 3: Uruchom Aplikację Flask

Otwórz drugi, oddzielny terminal w tym samym folderze i uruchom główną aplikację:

python app.py
