from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
#from flask_rq2 import RQ
from flask_migrate import Migrate

# Tworzymy puste instancje rozszerzeń
# Zostaną one połączone z aplikacją w app.py
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
#rq = RQ()
migrate = Migrate()

