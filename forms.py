from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, InputRequired
from models import User

# --- Formularze Uwierzytelniania (dla routes/auth.py) ---

class LoginForm(FlaskForm):
    """Formularz logowania."""
    email = StringField('E-mail', validators=[DataRequired(), Email(message="Podaj poprawny adres e-mail.")])
    password = PasswordField('Hasło', validators=[DataRequired(message="Hasło jest wymagane.")])
    remember = BooleanField('Zapamiętaj mnie')
    submit = SubmitField('Zaloguj się')


class RegisterForm(FlaskForm):
    """Formularz rejestracji."""
    name = StringField('Imię', validators=[DataRequired(), Length(min=2, max=100)])
    surname = StringField('Nazwisko', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('E-mail', validators=[DataRequired(), Email(message="Podaj poprawny adres e-mail.")])
    agency = StringField('Agencja', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Hasło', validators=[DataRequired(), Length(min=6, message="Hasło musi mieć co najmniej 6 znaków.")])
    # === POPRAWKA: Ujednolicona nazwa ===
    confirm_password = PasswordField(
        'Powtórz hasło', validators=[DataRequired(), EqualTo('password', message='Hasła muszą być takie same.')])
    accept_tos = BooleanField('Akceptuję regulamin', validators=[DataRequired(message='Musisz zaakceptować regulamin.')])
    submit = SubmitField('Zarejestruj się')

    def validate_email(self, email):
        """Sprawdza, czy e-mail nie jest już zajęty."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ten adres e-mail jest już zajęty. Proszę wybrać inny.')


class ResetRequestForm(FlaskForm):
    """Formularz żądania resetu hasła."""
    email = StringField('E-mail', validators=[DataRequired(), Email(message="Podaj poprawny adres e-mail.")])
    submit = SubmitField('Wyślij link do resetowania')

    def validate_email(self, email):
        """Sprawdza, czy konto z tym e-mailem istnieje."""
        user = User.query.filter_by(email=email.data).first()
        if not user:
            # Komunikat jest ogólny dla bezpieczeństwa (nie ujawnia, czy e-mail istnieje)
            raise ValidationError('Jeśli konto z tym adresem e-mail istnieje, wysłano na nie link.')


class ResetPasswordForm(FlaskForm):
    """Formularz ustawiania nowego hasła po resecie."""
    password = PasswordField('Nowe hasło', validators=[DataRequired(), Length(min=6, message="Hasło musi mieć co najmniej 6 znaków.")])
    confirm_password = PasswordField(
        'Powtórz nowe hasło', validators=[DataRequired(), EqualTo('password', message='Hasła muszą być takie same.')])
    submit = SubmitField('Zmień hasło')


# --- Formularze Profilu (dla routes/main.py) ---

class ChangePasswordForm(FlaskForm):
    """Formularz zmiany hasła w profilu użytkownika."""
    old_password = PasswordField('Stare hasło', validators=[DataRequired(message="Stare hasło jest wymagane.")])
    new_password = PasswordField('Nowe hasło', validators=[DataRequired(), Length(min=6, message="Hasło musi mieć co najmniej 6 znaków.")])
    # === POPRAWKA: Używamy 'confirm_password' aby pasowało do szablonu profile.html ===
    confirm_password = PasswordField(
        'Powtórz nowe hasło', validators=[DataRequired(), EqualTo('new_password', message='Nowe hasła muszą być takie same.')])
    submit_password = SubmitField('Zmień hasło')


class ChangeDetailsForm(FlaskForm):
    """Formularz zmiany danych osobowych w profilu."""
    name = StringField('Imię', validators=[DataRequired(), Length(min=2, max=100)])
    surname = StringField('Nazwisko', validators=[DataRequired(), Length(min=2, max=100)])
    agency = StringField('Agencja', validators=[DataRequired(), Length(min=2, max=150)])
    submit_details = SubmitField('Zapisz zmiany')


class ThemeForm(FlaskForm):
    """Formularz zmiany motywu."""
    theme = SelectField('Motyw', choices=[
        ('default', 'Domyślny Jasny'),
        ('default_dark', 'Domyślny Ciemny'),
    ], validators=[InputRequired()])
    submit_theme = SubmitField('Zmień motyw')


class RecipientForm(FlaskForm):
    """Formularz dodawania nowego odbiorcy e-mail."""
    email = StringField('E-mail odbiorcy', validators=[DataRequired(), Email(message="Podaj poprawny adres e-mail.")])
    submit_recipient = SubmitField('Dodaj odbiorcę')

