from sqlalchemy import func # Upewnij się, że masz ten import
from datetime import datetime, date, time, timezone # Dodano timezone

# Importuj 'db' z extensions, nie definiuj go tutaj!
from extensions import db

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous.exc import SignatureExpired, BadTimeSignature
from flask import current_app

class User(UserMixin, db.Model):
    __tablename__ = 'user' # Jawne zdefiniowanie nazwy tabeli
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    agency = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pracownik')
    # --- POPRAWKA UTC ---
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # --- KONIEC POPRAWKI ---
    accepted_tos = db.Column(db.Boolean, nullable=False, default=False)
    theme = db.Column(db.String(50), nullable=False, default='default')

    def set_password(self, password):
        """Generuje hash hasła i zapisuje go w bazie."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Sprawdza, czy podane hasło pasuje do hasha w bazie."""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        """Generuje bezpieczny, czasowy token do resetowania hasła."""
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Weryfikuje token resetowania hasła i zwraca użytkownika."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expires_sec)
            user_id = data.get('user_id')
        except (SignatureExpired, BadTimeSignature):
            return None
        # Zwracamy obiekt User zamiast tylko ID
        return db.session.get(User, user_id) # Użyj nowszej metody get

class Trip(db.Model):
    __tablename__ = 'trip'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    trip_date = db.Column(db.Date, nullable=False, index=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    spots = db.Column(db.Integer, nullable=True, default=1) # Zmieniono default na 1
    start_time = db.Column(db.Time, nullable=True)
    departure_time = db.Column(db.Time, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    work_start_time = db.Column(db.Time, nullable=True)
    work_end_time = db.Column(db.Time, nullable=True)
    kilometers = db.Column(db.Float, nullable=True)
    manager_was_passenger = db.Column(db.Boolean, default=False, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True) # Dodano index
    # --- POPRAWKA UTC ---
    last_modified = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # --- KONIEC POPRAWKI ---

    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Można ustawić ondelete='SET NULL'
    manager = db.relationship('User', backref='managed_trips')

class Signup(db.Model):
    __tablename__ = 'signup'
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id', ondelete='CASCADE'), nullable=False, index=True) # Dodano index
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True) # Dodano index
    status = db.Column(db.String(50), nullable=False)

    trip = db.relationship('Trip', backref=db.backref('signups', cascade="all, delete-orphan", lazy='joined')) # Dodano lazy='joined'
    user = db.relationship('User', backref=db.backref('signups', cascade="all, delete-orphan", lazy='joined')) # Dodano lazy='joined'

class Recipient(db.Model):
    __tablename__ = 'recipient'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True) # Dodano index

    user = db.relationship('User', backref=db.backref('recipients', cascade="all, delete-orphan"))

