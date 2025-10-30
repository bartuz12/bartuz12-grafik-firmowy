"""
Trasy (routes) dla głównych funkcji aplikacji (dashboard, profil)
Plik: routes/main.py
"""
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from models import db, User, Recipient, Trip
# Importujemy formularze z pliku forms.py
from forms import ChangePasswordForm, ChangeDetailsForm, ThemeForm, RecipientForm

main_bp = Blueprint('main', __name__)


# ==================== TRASY GŁÓWNE ====================

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Wyświetla główny panel (dashboard) po zalogowaniu."""
    return render_template(
        'dashboard.html',
        title="Panel Główny"
    )

@main_bp.route('/privacy-policy')
def privacy_policy():
    """Wyświetla stronę polityki prywatności."""
    return render_template('privacy_policy.html', title="Polityka Prywatności")


# ==================== TRASY PROFILU UŻYTKOWNIKA ====================

@main_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """Wyświetla stronę profilu użytkownika."""
    # Tworzymy instancje formularzy, aby przekazać je do szablonu
    password_form = ChangePasswordForm()
    details_form = ChangeDetailsForm(obj=current_user) # Wypełnij formularz aktualnymi danymi
    theme_form = ThemeForm(data={'theme': current_user.theme or 'default'})
    recipient_form = RecipientForm()
    
    # Pobierz listę odbiorców dla bieżącego użytkownika
    recipients = Recipient.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'profile.html',
        title="Mój Profil",
        password_form=password_form,
        details_form=details_form,
        theme_form=theme_form,
        recipient_form=recipient_form,
        recipients=recipients
    )

# === POPRAWKA: Dodajemy jawny 'endpoint', aby pasował do szablonów ===
@main_bp.route('/profile/change-password', methods=['POST'], endpoint='change_password')
@login_required
def profile_change_password():
    """Obsługuje formularz zmiany hasła."""
    # Załaduj wszystkie formularze, aby móc je zwrócić w razie błędu
    password_form = ChangePasswordForm() # Pobierz dane z request.form
    details_form = ChangeDetailsForm(obj=current_user)
    theme_form = ThemeForm(data={'theme': current_user.theme or 'default'})
    recipient_form = RecipientForm()
    recipients = Recipient.query.filter_by(user_id=current_user.id).all()

    if password_form.validate_on_submit():
        if current_user.check_password(password_form.old_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Hasło zostało pomyślnie zaktualizowane.', 'success')
            return redirect(url_for('main.profile'))
        else:
            flash('Nieprawidłowe stare hasło.', 'error')
    else:
        # Przechwyć błędy walidacji (np. niezgodne hasła)
        for field, errors in password_form.errors.items():
            for error in errors:
                flash(f"Błąd walidacji: {error}", 'error')

    # Jeśli formularz nie przeszedł walidacji, renderuj stronę profilu ponownie
    return render_template(
        'profile.html',
        title="Mój Profil",
        password_form=password_form,
        details_form=details_form,
        theme_form=theme_form,
        recipient_form=recipient_form,
        recipients=recipients
    )

# === POPRAWKA: Dodajemy jawny 'endpoint', aby pasował do szablonów ===
@main_bp.route('/profile/update-details', methods=['POST'], endpoint='update_details')
@login_required
def profile_update_details():
    """Obsługuje formularz zmiany danych osobowych."""
    details_form = ChangeDetailsForm() # Pobierz dane z request.form
    
    # Przeładuj inne formularze na wypadek błędu renderowania
    password_form = ChangePasswordForm()
    theme_form = ThemeForm(data={'theme': current_user.theme or 'default'})
    recipient_form = RecipientForm()
    recipients = Recipient.query.filter_by(user_id=current_user.id).all()

    if details_form.validate_on_submit():
        current_user.name = details_form.name.data
        current_user.surname = details_form.surname.data
        current_user.agency = details_form.agency.data
        db.session.commit()
        flash('Dane profilu zostały zaktualizowane.', 'success')
        return redirect(url_for('main.profile'))
    else:
        for field, errors in details_form.errors.items():
            for error in errors:
                flash(f"Błąd walidacji: {error}", 'error')
    
    return render_template(
        'profile.html',
        title="Mój Profil",
        password_form=password_form,
        details_form=details_form,
        theme_form=theme_form,
        recipient_form=recipient_form,
        recipients=recipients
    )

# === POPRAWKA: Dodajemy jawny 'endpoint', aby pasował do szablonów ===
@main_bp.route('/profile/change-theme', methods=['POST'], endpoint='change_theme')
@login_required
def profile_change_theme():
    """Obsługuje formularz zmiany motywu."""
    theme_form = ThemeForm() # Pobierz dane z request.form

    if theme_form.validate_on_submit():
        current_user.theme = theme_form.theme.data
        db.session.commit()
        flash('Motyw został zaktualizowany.', 'success')
    else:
        flash('Wystąpił błąd podczas zmiany motywu.', 'error')

    return redirect(url_for('main.profile'))

# === POPRAWKA: Dodajemy jawny 'endpoint', aby pasował do szablonów ===
@main_bp.route('/profile/add-recipient', methods=['POST'], endpoint='add_recipient')
@login_required
def profile_add_recipient():
    """Obsługuje formularz dodawania odbiorcy e-mail."""
    recipient_form = RecipientForm() # Pobierz dane z request.form

    if recipient_form.validate_on_submit():
        new_recipient = Recipient(
            email=recipient_form.email.data,
            user_id=current_user.id
        )
        db.session.add(new_recipient)
        db.session.commit()
        flash('Dodano nowego odbiorcę.', 'success')
    else:
        for field, errors in recipient_form.errors.items():
            for error in errors:
                flash(f"Błąd walidacji: {error}", 'error')

    return redirect(url_for('main.profile'))

# === POPRAWKA: Zmieniamy nazwę trasy, aby pasowała do testów i szablonu ===
@main_bp.route('/profile/delete-recipient/<int:recipient_id>', methods=['POST'], endpoint='delete_recipient')
@login_required
def profile_delete_recipient(recipient_id):
    """Obsługuje usuwanie odbiorcy e-mail."""
    recipient = Recipient.query.filter_by(id=recipient_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(recipient)
        db.session.commit()
        flash('Odbiorca został usunięty.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Nie można usunąć odbiorcy: {e}', 'error')
        current_app.logger.error(f'Błąd podczas usuwania odbiorcy (ID: {recipient_id}): {e}')

    return redirect(url_for('main.profile'))


# ==================== TRASY API (dla kalendarza) ====================

@main_bp.route('/api/events')
@login_required
def api_events():
    """
    Zwraca listę zleceń w formacie JSON dla kalendarza (FullCalendar).
    """
    try:
        trips = Trip.query.filter_by(is_archived=False).all()
        
        events = []
        for trip in trips:
            events.append({
                'id': trip.id,
                'title': trip.title,
                'start': trip.trip_date.isoformat(), # Wymagany format YYYY-MM-DD
            })
        return jsonify(events)
    except Exception as e:
        current_app.logger.error(f"Błąd w api_events: {e}")
        return jsonify({"error": "Błąd serwera"}), 500

@main_bp.route('/api/trip-details-fragment/<int:trip_id>')
@login_required
def api_trip_details_fragment(trip_id):
    """
    Zwraca dane o zleceniu jako JSON (lub renderuje fragment HTML).
    """
    trip = db.session.get(Trip, trip_id)
    if not trip:
        return jsonify({'error': 'Zlecenie nie znalezione'}), 404
    
    # Na razie zwracamy prosty JSON, aby naprawić błąd.
    return jsonify({
        'id': trip.id,
        'title': trip.title,
        'date': trip.trip_date.isoformat(),
        'notes': trip.notes or ""
    })

# === POPRAWKA: Dodanie brakującej trasy, która powodowała błąd w `profile.html` ===
@main_bp.route('/profile/change-agency', methods=['POST'], endpoint='change_agency')
@login_required
def profile_change_agency():
    """Obsługuje formularz zmiany agencji (jeśli jest używany)."""
    # Ta funkcja jest wymagana przez `url_for('main.change_agency')` w `profile.html`
    
    new_agency = request.form.get('agency') # Używamy 'agency' z ChangeDetailsForm
    if new_agency and len(new_agency) >= 2 and len(new_agency) <= 150:
        current_user.agency = new_agency
        db.session.commit()
        flash('Agencja została zaktualizowana.', 'success')
    else:
        # Błąd walidacji lub brak danych
        flash('Błąd podczas aktualizacji agencji.', 'error')
        
    return redirect(url_for('main.profile'))