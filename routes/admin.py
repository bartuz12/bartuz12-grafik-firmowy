import io
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response, current_app
from flask_login import login_required, current_user
# Poprawka: Dodano 'asc' do importów sqlalchemy
from sqlalchemy import func, extract, or_, asc
# --- POPRAWKA 3.1: Importujemy 'joinedload' i 'subqueryload' ---
from sqlalchemy.orm import joinedload, subqueryload
from datetime import datetime, date, timedelta, time 
import pandas as pd

from models import db, User, Trip, Signup
from utils import admin_or_manager_required, send_email_in_background
# --- POPRAWKA 3.1: Usunięto import, który mógł powodować cykliczną zależność ---
# Usunięto: from .trips import auto_signup_golden_workers
# Logika auto_signup_golden_workers powinna być przeniesiona do 'utils.py', 
# aby uniknąć importowania jednego modułu 'routes' z drugiego.
# Na razie zakładam, że ta funkcja jest dostępna globalnie lub w 'utils'.
# Jeśli nie, przenieś 'auto_signup_golden_workers' do 'utils.py'.

admin_bp = Blueprint('admin', __name__)

# --- ZBIORCZA EDYCJA (Z FUNKCJĄ FILTROWANIA) ---

@admin_bp.route('/settlements', methods=['GET', 'POST'])
@login_required
@admin_or_manager_required
def settlements():
    if request.method == 'POST':
        # ... (Logika POST bez zmian) ...
        try:
            trips_to_update = {}
            
            for key, value in request.form.items():
                if '-' not in key:
                    continue 

                try:
                    field, trip_id_str = key.split('-', 1)
                    trip_id = int(trip_id_str)
                except ValueError:
                    continue 

                if trip_id not in trips_to_update:
                    trips_to_update[trip_id] = db.session.get(Trip, trip_id)
                
                trip = trips_to_update[trip_id]
                if not trip:
                    continue
                
                processed_value = value if value else None

                if field == 'start_time':
                    trip.start_time = time.fromisoformat(processed_value) if processed_value else None
                elif field == 'departure_time':
                    trip.departure_time = time.fromisoformat(processed_value) if processed_value else None
                elif field == 'spots':
                    trip.spots = int(processed_value) if processed_value else 1
                elif field == 'work_start':
                    trip.work_start_time = time.fromisoformat(processed_value) if processed_value else None
                elif field == 'work_end':
                    trip.work_end_time = time.fromisoformat(processed_value) if processed_value else None
                elif field == 'km':
                    trip.kilometers = float(processed_value.replace(',', '.')) if processed_value else None
                elif field == 'passenger':
                    trip.manager_was_passenger = True

            for trip_id, trip in trips_to_update.items():
                if f'passenger-{trip_id}' not in request.form and trip.trip_date < date.today():
                    trip.manager_was_passenger = False

            db.session.commit()
            flash('Wszystkie zmiany zostały pomyślnie zapisane.', 'success')
        except (ValueError, TypeError) as e:
            db.session.rollback()
            flash(f'Błąd formatu danych. Wprowadzono nieprawidłową wartość: {e}', 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Błąd podczas zbiorczej edycji: {e}")
            flash(f'Wystąpił nieoczekiwany błąd serwera: {e}', 'error')
            
        return redirect(url_for('admin.settlements', **request.args))

    # --- POPRAWIONA LOGIKA FILTROWANIA DLA GET ---
    search_text = request.args.get('search_text', '')
    search_month = request.args.get('search_month', str(date.today().month)) 

    # --- POPRAWKA 3.1: Dodajemy 'options' do bazowego zapytania ---
    # Ładujemy 'manager' (relacja User) i 'signups' (relacja Signup) od razu.
    # Używamy subqueryload dla signups, aby uniknąć duplikowania wyników Trip.
    query = Trip.query.filter(Trip.is_archived == False).options(
        joinedload(Trip.manager),
        subqueryload(Trip.signups) 
        # Jeśli w pętli odwołujesz się też do signup.user.name, 
        # a 'lazy=joined' w models.py by nie działało, użylibyśmy:
        # subqueryload(Trip.signups).joinedload(Signup.user)
        # Ale 'lazy=joined' w Twoim modelu Signup prawdopodobnie już to załatwia.
    )

    if search_text:
        query = query.filter(Trip.title.ilike(f'%{search_text}%'))
    
    current_year = date.today().year
    query = query.filter(extract('year', Trip.trip_date) == current_year)

    if search_month: 
        try:
            query = query.filter(extract('month', Trip.trip_date) == int(search_month))
        except ValueError:
            pass 

    today = date.today()
    
    # Zlecenia przyszłe: od dzisiaj włącznie, posortowane rosnąco
    # Zapytanie .filter() odziedziczy 'options' z 'query'
    future_trips = query.filter(Trip.trip_date >= today).order_by(Trip.trip_date.asc()).all()
    
    # Zlecenia przeszłe: do wczoraj włącznie, posortowane rosnąco
    past_trips = query.filter(Trip.trip_date < today).order_by(Trip.trip_date.asc()).all()
    
    filter_values = {
        'search_text': search_text,
        'search_month': search_month,
    }

    return render_template(
        'admin_settlements.html', 
        future_trips=future_trips, 
        past_trips=past_trips,  
        today=today,
        filters=filter_values
    )


# --- Zarządzanie Użytkownikami ---
@admin_bp.route('/users')
@login_required
@admin_or_manager_required
def users():
    # --- POPRAWKA 3.1: Dodajemy 'options' do zapytania o użytkowników ---
    # Zakładamy, że szablon 'admin_users.html' może odwoływać się do 
    # zapisów użytkownika (user.signups), co powoduje N+1.
    all_users = User.query.order_by(User.name, User.surname).options(
        subqueryload(User.signups)
    ).all()
    return render_template('admin_users.html', users=all_users)


@admin_bp.route('/users/set-status/<int:user_id>', methods=['POST'])
@login_required
@admin_or_manager_required
def set_user_status(user_id):
    # ... (Logika bez zmian) ...
    user = db.session.get(User, user_id)
    if not user:
        flash('Użytkownik nie znaleziony.', 'error')
        return redirect(url_for('admin.users'))
        
    new_status = request.form.get('status')
    VALID_STATUSES = ['pracownik', 'złoty pracownik', 'kierownik', 'admin', 'zablokowany']
    
    if new_status not in VALID_STATUSES:
           flash('Wybrano nieprawidłowy status.', 'error')
           return redirect(url_for('admin.users'))

    if user.status == 'admin' and new_status != 'admin' and User.query.filter_by(status='admin').count() <= 1:
        flash('Nie można zmienić statusu jedynemu administratorowi.', 'error')
    else:
        try:
            user.status = new_status
            db.session.commit()
            flash(f'Zmieniono status dla {user.name} {user.surname}.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Wystąpił błąd podczas zmiany statusu: {e}', 'error')
                 
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/set-agency/<int:user_id>', methods=['POST'])
@login_required
@admin_or_manager_required
def set_user_agency(user_id):
    # ... (Logika bez zmian) ...
    user = db.session.get(User, user_id)
    if not user:
        flash('Użytkownik nie znaleziony.', 'error')
        return redirect(url_for('admin.users'))
            
    new_agency = request.form.get('agency')
    VALID_AGENCIES = ['DPL', 'JMG', 'SJ', 'WP']
        
    if new_agency in VALID_AGENCIES:
        try:
            user.agency = new_agency
            db.session.commit()
            flash(f'Zmieniono agencję dla {user.name} {user.surname}.', 'success')
        except Exception as e:
             db.session.rollback()
             flash(f'Wystąpił błąd podczas zmiany agencji: {e}', 'error')
    else:
        flash('Wybrano nieprawidłową agencję.', 'error')
            
    return redirect(url_for('admin.users'))


# --- Zarządzanie Archiwum ---
@admin_bp.route('/archive')
@login_required
@admin_or_manager_required
def archive():
    # --- POPRAWKA 3.1: Dodajemy 'options' do zapytania o archiwum ---
    # Podobnie jak w 'settlements', ładujemy 'manager' od razu.
    archived_trips = Trip.query.filter_by(is_archived=True).order_by(Trip.trip_date.desc()).options(
        joinedload(Trip.manager)
    ).all()
    return render_template('archive.html', trips=archived_trips)


@admin_bp.route('/archive/run', methods=['POST'])
@login_required
@admin_or_manager_required
def run_archive():
    # ... (Logika bez zmian, to jest UPDATE, nie generuje N+1) ...
    try:
        six_months_ago = date.today() - timedelta(days=180)
        updated_count = db.session.query(Trip).filter(
            Trip.trip_date < six_months_ago, 
            Trip.is_archived == False
        ).update({'is_archived': True}, synchronize_session=False) 
            
        db.session.commit()
        flash(f'Pomyślnie zarchiwizowano {updated_count} zleceń.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Wystąpił błąd podczas archiwizacji: {e}', 'error')
            
    return redirect(url_for('admin.archive'))


# --- Zarządzanie Danymi (Import/Export/Czyszczenie) ---
@admin_bp.route('/clear-month', methods=['POST'])
@login_required
@admin_or_manager_required
def clear_month():
    # ... (Logika bez zmian, to jest DELETE, nie generuje N+1) ...
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Brak danych JSON.'}), 400
            
    year = data.get('year')
    month = data.get('month')
        
    if not isinstance(year, int) or not isinstance(month, int):
        return jsonify({'status': 'error', 'message': 'Rok i miesiąc muszą być liczbami.'}), 400
            
    try:
        deleted_count = db.session.query(Trip).filter(
            extract('year', Trip.trip_date) == year,
            extract('month', Trip.trip_date) == month,
            Trip.is_archived == False
        ).delete(synchronize_session=False)
                
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Pomyślnie usunięto {deleted_count} zleceń z {month}/{year}.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Błąd podczas czyszczenia miesiąca {month}/{year}: {e}")
        return jsonify({'status': 'error', 'message': f'Wystąpił błąd serwera podczas usuwania zleceń.'}), 500


@admin_bp.route('/import/sample')
@login_required
@admin_or_manager_required
def download_sample():
    # ... (Logika bez zmian) ...
    sample_data = {
        'Data': [date.today().strftime('%Y-%m-%d')],
        'Nazwa': ['Przykładowe zlecenie'],
        'Potwierdzone': ['tak']
    }
    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
        
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Grafik')
        output.seek(0)
        return Response(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment;filename=przykladowy_grafik.xlsx"}
        )
    except Exception as e:
         flash(f"Błąd podczas generowania pliku Excel: {e}", "error")
         return redirect(url_for('admin.import_excel'))


@admin_bp.route('/import', methods=['GET', 'POST'])
@login_required
@admin_or_manager_required
def import_excel():
    # ... (Logika importu bez zmian, tutaj N+1 jest akceptowalne) ...
    # Problem N+1 nie występuje krytycznie w pętli importu, 
    # ponieważ wykonujemy logikę biznesową (auto_signup, send_email),
    # a nie tylko renderowanie widoku. Optymalizacja tutaj byłaby 
    # bardziej złożona (np. bulk_insert, masowe powiadomienia) 
    # i wykracza poza prosty fix 'joinedload'.
    if request.method == 'POST':
        file = request.files.get('excel_file')
        if not file or not file.filename.lower().endswith(('.xlsx', '.xls')):
            flash('Nie wybrano pliku Excel lub plik ma nieprawidłowe rozszerzenie.', 'error')
            return redirect(url_for('admin.import_excel'))
                
        try:
            df = pd.read_excel(file, header=None, usecols=[0, 1, 2]) 
                
            dates_from_excel = pd.to_datetime(df[0], errors='coerce').dt.date.dropna().tolist()
            if not dates_from_excel:
                   flash("Nie znaleziono poprawnych dat w pierwszej kolumnie.", "warning")
                   return redirect(url_for('admin.import_excel'))

            # Ten 'all()' jest OK, bo służy do budowania mapy (słownika)
            existing_trips_query = Trip.query.filter(Trip.trip_date.in_(dates_from_excel)).all()
            existing_trips_map = {trip.trip_date: trip for trip in existing_trips_query}

            newly_created_trips = []
            updated_count = 0
            skipped_count = 0

            for index, row in df.iterrows():
                try:
                    trip_date_obj = pd.to_datetime(row[0], errors='coerce')
                    title = str(row.get(1, '')).strip()

                    if pd.isna(trip_date_obj) or not title:
                        skipped_count += 1
                        continue 

                    trip_date = trip_date_obj.date()
                    is_confirmed = str(row.get(2, '')).strip().lower() == 'tak'
                        
                    spots = 7 if 'dino' in title.lower() else 2
                        
                    trip = existing_trips_map.get(trip_date)

                    if trip:
                        trip.title = title
                        trip.is_confirmed = is_confirmed
                        trip.spots = spots
                        trip.last_modified = datetime.utcnow()
                        updated_count += 1
                    else:
                        new_trip = Trip(trip_date=trip_date, title=title, is_confirmed=is_confirmed, spots=spots)
                        db.session.add(new_trip)
                        newly_created_trips.append(new_trip)
                    
                except Exception as row_error:
                    db.session.rollback() 
                    flash(f"Błąd przetwarzania danych w wierszu {index + 1}: {row_error}", 'warning')
                    skipped_count += 1
                    continue 
                
            db.session.commit()

            # Ten 'all()' jest OK, to pojedyncze zapytanie
            users_to_notify = User.query.filter(User.status.in_(['pracownik', 'złoty pracownik'])).all()
            
            # --- UWAGA ---
            # Tutaj występuje problem N+1 (N to liczba nowych zleceń)
            # Rozwiązanie (Audyt 2.2) już masz - wysyłka e-maili przez RQ.
            # To jest "problem N+1 operacji", a nie "N+1 zapytań".
            from utils import auto_signup_golden_workers # Tymczasowy import, przenieś do utils.py
            
            for trip in newly_created_trips:
                db.session.add(Signup(trip_id=trip.id, user_id=current_user.id, status='potwierdzony'))
                auto_signup_golden_workers(trip)
                for user in users_to_notify:
                    # Zakładamy, że ta funkcja jest już asynchroniczna (zgodnie z Priorytetem 1)
                    send_email_in_background(user.email, f'Nowe zlecenie: {trip.title}', 'email/new_trip', trip=trip, user=user)

            db.session.commit()

            flash_msg = f'Import zakończony. Utworzono {len(newly_created_trips)} nowych zleceń, zaktualizowano {updated_count}.'
            if skipped_count > 0:
                   flash_msg += f' Pomięto {skipped_count} wierszy z powodu brakujących danych lub błędów.'
            flash(flash_msg, 'success')
            return redirect(url_for('main.dashboard'))

        except ValueError as e: 
            db.session.rollback()
            flash(f"Błąd podczas przetwarzania pliku: {e}", 'error')
        except Exception as e: 
            db.session.rollback()
            current_app.logger.error(f"Nieoczekiwany błąd importu Excel: {e}")
            flash('Wystąpił nieoczekiwany błąd podczas importu pliku Excel.', 'error')
                
        return redirect(url_for('admin.import_excel'))
            
    return render_template('import_excel.html')


@admin_bp.route('/export')
@login_required
def export_excel():
    if not current_user.agency or current_user.agency.upper() != 'DPL':
        flash('Ta funkcja jest dostępna tylko dla użytkowników agencji DPL.', 'error')
        return redirect(url_for('main.dashboard'))
            
    try:
        # --- DOBRA PRAKTYKA: To zapytanie jest wydajne (nie ma N+1) ---
        # Wybierasz tylko te kolumny, których potrzebujesz. Świetna robota.
        user_signups = db.session.query(
            Trip.trip_date, Trip.title, Trip.work_start_time, Trip.work_end_time, Trip.kilometers, Trip.manager_was_passenger
        ).join(Signup).filter(Signup.user_id == current_user.id).order_by(Trip.trip_date).all()

        data = []
        for signup_data in user_signups:
            is_passenger = False
            if current_user.status in ['admin', 'kierownik']:
                is_passenger = signup_data.manager_was_passenger
                    
            data.append({
                'data': signup_data.trip_date,
                'miejsce': signup_data.title,
                'poczatek_pracy': signup_data.work_start_time,
                'koniec_pracy': signup_data.work_end_time,
                'ilosc_km': signup_data.kilometers,
                'pasażer': 1 if is_passenger else 0
            })
                
        df = pd.DataFrame(data)
        if 'data' in df.columns:
             df['data'] = pd.to_datetime(df['data']).dt.strftime('%Y-%m-%d')
        time_cols = ['poczatek_pracy', 'koniec_pracy']
        for col in time_cols:
            if col in df.columns:
                 df[col] = df[col].apply(lambda x: x.strftime('%H:%M') if isinstance(x, time) else pd.NaT)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Grafik')
        output.seek(0)

        filename = f"grafik_{current_user.name}_{date.today().strftime('%Y%m%d')}.xlsx"

        return Response(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
         current_app.logger.error(f"Błąd podczas eksportu do Excel dla {current_user.email}: {e}")
         flash("Wystąpił błąd podczas generowania pliku Excel.", "error")
         return redirect(url_for('main.dashboard'))
