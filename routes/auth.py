from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app # <-- Dodano import current_app
# --- POPRAWKA ---
# Dodano 'login_required' do importu, co naprawia błąd 'NameError'
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime

# Importujemy obiekty z głównych plików aplikacji
# --- POPRAWKA: Importujemy 'rq' z extensions ---
from extensions import db, rq
from models import User
from utils import send_email_in_background
# Importujemy klasy formularzy z forms.py
from forms import LoginForm, RegisterForm, ResetRequestForm, ResetPasswordForm

# Tworzymy Blueprint o nazwie 'auth'
auth_bp = Blueprint('auth', __name__)

# --- Trasy Związane z Uwierzytelnianiem ---

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegisterForm() # Używamy klasy formularza

    # form.validate_on_submit() sprawdza zarówno metodę POST, jak i walidację + CSRF
    if form.validate_on_submit():
        # Wszystkie dane są poprawne, pochodzą z form.data
        new_user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            agency=form.agency.data,
            accepted_tos=form.accept_tos.data
        )
        new_user.set_password(form.password.data)

        if User.query.count() == 0:
            new_user.status = 'admin'

        try:
            db.session.add(new_user)
            db.session.commit()

            # --- POPRAWKA: Używamy rq.get_queue().enqueue ---
            try:
                rq.get_queue().enqueue(
                    send_email_in_background,
                    new_user.email,
                    'Witaj w Grafiku!',
                    'email/welcome',
                    user=new_user
                )
            except Exception as e:
                # Logowanie błędu kolejki, ale kontynuacja rejestracji
                current_app.logger.error(f"Nie udało się zakolejkować e-maila powitalnego: {e}")
                flash('Rejestracja pomyślna, ale wystąpił problem z wysyłką e-maila powitalnego.', 'warning')
                return redirect(url_for('auth.login'))

            flash('Rejestracja pomyślna! Możesz się teraz zalogować.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            # Logowanie błędu bazy danych
            current_app.logger.error(f"Błąd bazy danych podczas rejestracji: {e}") # <-- Poprawiono NameError
            flash(f'Wystąpił błąd podczas rejestracji: {e}', 'error')
            # Ponowne renderowanie formularza z błędami

    # Gdy metoda GET lub walidacja nie powiedzie się
    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm() # Używamy klasy formularza

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user or not user.check_password(form.password.data):
            # Flash będzie wyświetlony po przekierowaniu, ale musimy użyć redirect dla Flask-WTF
            flash('Nieprawidłowy e-mail lub hasło.', 'error')
            return redirect(url_for('auth.login'))

        if user.status == 'zablokowany':
            flash('Twoje konto jest zablokowane. Skontaktuj się z administratorem.', 'error')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember.data) # Odczytanie stanu checkboxa "zapamiętaj mnie"

        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.dashboard'))

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś pomyślnie wylogowany.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = ResetRequestForm() # Używamy klasy formularza

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for('auth.reset_token', token=token, _external=True)

            # --- POPRAWKA: Używamy rq.get_queue().enqueue ---
            try:
                rq.get_queue().enqueue(
                    send_email_in_background,
                    user.email,
                    'Resetowanie hasła - Grafik',
                    'email/reset_password',
                    user=user,
                    reset_url=reset_url
                )
            except Exception as e:
                current_app.logger.error(f"Nie udało się zakolejkować e-maila resetującego hasło: {e}")
                # Nadal pokazujemy komunikat sukcesu, aby nie ujawniać istnienia konta
                flash('Jeśli konto istnieje, wysłano instrukcję resetowania hasła (problem z wysyłką).', 'warning')
                return redirect(url_for('auth.login'))

        flash('Jeśli konto istnieje, wysłano instrukcję resetowania hasła.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('reset_request.html', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('Link do resetowania hasła jest nieprawidłowy lub wygasł.', 'error')
        return redirect(url_for('auth.reset_request'))

    form = ResetPasswordForm() # Używamy klasy formularza

    if form.validate_on_submit():
        try:
            user.set_password(form.password.data)
            db.session.commit()
            flash('Twoje hasło zostało zaktualizowane! Możesz się teraz zalogować.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Błąd podczas zmiany hasła po resecie: {e}") # <-- Poprawiono NameError
            flash(f'Wystąpił błąd podczas zmiany hasła: {e}', 'error')
            # Ponowne renderowanie formularza z tokenem, aby użytkownik mógł spróbować ponownie
            return render_template('reset_token.html', form=form, token=token)

    return render_template('reset_token.html', form=form, token=token)