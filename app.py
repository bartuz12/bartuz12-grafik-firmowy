import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, current_app
from config import Config, TestConfig
from extensions import db, login_manager, mail, csrf, rq, migrate
from utils import nl2br_filter, inject_current_year, url_for_static_bust # Wszystkie funkcje pomocnicze
from routes.auth import auth_bp
from routes.main import main_bp
from routes.trips import trips_bp
from routes.admin import admin_bp
from models import User # Potrzebne do ładowania użytkownika

def create_app(config_class=Config):
    """
    Wzorzec fabryki aplikacji (Application Factory).
    """
    app = Flask(__name__)
    
    # Używamy TestConfig tylko, jeśli jesteśmy w pytest (zapewnia czystą bazę w pamięci)
    if os.environ.get('FLASK_TESTING') == 'True':
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(config_class)

    # --- 1. INICJALIZACJA ROZSZERZEŃ ---
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    rq.init_app(app)
    migrate.init_app(app, db) # Potrzebne do migracji bazy danych

    # --- 2. REJESTRACJA FUNKCJI W JINJA ---
    with app.app_context():
        # Context Processor: Przekazuje zmienne do kontekstu wszystkich szablonów
        app.context_processor(inject_current_year)
        
        # Filtr: Rejestruje filtr nl2br
        app.jinja_env.filters['nl2br'] = nl2br_filter
        
        # Funkcja Globalna: Rejestruje funkcję cache-busting
        app.jinja_env.globals.update(url_for_static_bust=url_for_static_bust)

    # --- 3. REJESTRACJA MODUŁÓW (BLUEPRINTS) ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(trips_bp, url_prefix='/trip')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # --- 4. FLASK-LOGIN KONFIGURACJA ---
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Proszę się zalogować, aby uzyskać dostęp do tej strony."
    login_manager.login_message_category = "info"
    
    @login_manager.user_loader
    def load_user(user_id):
        # Używamy db.session.get (nowa metoda) zamiast query.get
        return db.session.get(User, int(user_id))

    # --- 5. LOGOWANIE DO PLIKU (AUDYT 3.3) ---
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Ustawia logowanie błędów do pliku logs/grafik.log (z rotacją)
        file_handler = RotatingFileHandler('logs/grafik.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Grafik startup')

    # --- 6. HANDLERY BŁĘDÓW (AUDYT 3.2) ---
    # Logowanie błędów 404 dla informacji
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.info(f"Strona nie znaleziona: {request.path} (404)")
        return render_template('404.html'), 404

    # Logowanie błędów serwera 500 (krytyczne)
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback() # Zawsze cofnij transakcję bazy danych
        app.logger.error(f"BŁĄD SERWERA 500: {error}")
        return render_template('500.html'), 500

    return app

# --- PLIK URUCHOMIENIOWY (WYŁĄCZNIE DLA PROCESU WSGI LUB LOKALNEGO DEBUGOWANIA) ---
# Wersja produkcyjna jest uruchamiana przez Gunicorn, np. 'gunicorn run:app'
if __name__ == '__main__':
    # Ta sekcja zostanie usunięta na produkcji (Audyt 2.4)
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
