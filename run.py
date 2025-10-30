from app import create_app
import os

# Wczytujemy konfigurację ze zmiennej środowiskowej lub używamy domyślnej
config_name = os.getenv('FLASK_CONFIG', 'config.Config')

# Tworzymy instancję aplikacji
app = create_app(config_name)

# Ten blok służy TYLKO do uruchamiania lokalnego serwera deweloperskiego
# np. poleceniem `python run.py`
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    port = int(os.environ.get('PORT', 5001))
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

