// Ten plik inicjalizuje kalendarz i obsługuje globalne funkcje (modale).

document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.log("Element #calendar nie znaleziony, skrypt dashboard_main.js kończy działanie.");
        return; 
    }

    // Odczytaj dane konfiguracyjne z atrybutów data-* elementu kalendarza
    const eventsUrl = calendarEl.dataset.eventsUrl;
    const detailsUrlTemplate = calendarEl.dataset.detailsUrlTemplate;
    const clearMonthUrl = calendarEl.dataset.clearMonthUrl;
    const userStatus = calendarEl.dataset.userStatus;
    const isAdmin = (userStatus === 'admin' || userStatus === 'kierownik');

    // --- Obsługa Okien Modalnych ---
    const detailsModal = document.getElementById('details-modal');
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalClose = document.getElementById('modal-close');
    const confirmModal = document.getElementById('confirm-modal');
    const confirmModalTitle = document.getElementById('confirm-modal-title');
    const confirmModalBody = document.getElementById('confirm-modal-body');
    const confirmModalOk = document.getElementById('confirm-modal-ok');
    const confirmModalCancel = document.getElementById('confirm-modal-cancel');

    // Funkcje do pokazywania/ukrywania modali (dostępne globalnie przez window)
    window.showModal = function(modalElement) {
        if (modalBackdrop && modalElement) {
            modalBackdrop.style.display = 'block';
            modalElement.style.display = 'flex';
        }
    }
    window.hideAllModals = function() {
        if (modalBackdrop && detailsModal && confirmModal) {
            modalBackdrop.style.display = 'none';
            detailsModal.style.display = 'none';
            confirmModal.style.display = 'none';
        }
    }
    // Zamknij modal po kliknięciu X lub tła
    if(modalClose) modalClose.addEventListener('click', hideAllModals);
    if(modalBackdrop) modalBackdrop.addEventListener('click', hideAllModals);
    // Zamknij modal po naciśnięciu Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape") hideAllModals();
    });

    // Funkcja do wczytywania zawartości do modala szczegółów
    window.showDetailsModalWithUrl = function(url, title) {
        if (!detailsModal || !modalTitle || !modalBody) return;
        modalTitle.textContent = title;
        modalBody.innerHTML = '<div class="modal-loader">Ładowanie...</div>';
        showModal(detailsModal);
        
        fetch(url)
            .then(response => response.ok ? response.text() : Promise.reject('Network response was not ok'))
            .then(htmlFragment => { modalBody.innerHTML = htmlFragment; })
            .catch(err => { modalBody.innerHTML = '<p style="color: red;">Wystąpił błąd podczas ładowania danych.</p>'; console.error(err); });
    }
    
    // Funkcja do wyświetlania modala potwierdzającego
    window.showConfirmation = function(options) {
        if (!confirmModal || !confirmModalTitle || !confirmModalBody || !confirmModalOk || !confirmModalCancel) return;
        confirmModalTitle.textContent = options.title;
        confirmModalBody.innerHTML = options.body;
        showModal(confirmModal);

        const newOkButton = confirmModalOk.cloneNode(true);
        confirmModalOk.parentNode.replaceChild(newOkButton, confirmModalOk);
        
        newOkButton.addEventListener('click', () => { hideAllModals(); options.onOk(); });
        confirmModalCancel.addEventListener('click', hideAllModals, { once: true }); // Użyj 'once' dla przycisku Anuluj
    }
    
    // --- Funkcja do obsługi zapisu (teraz używana tylko przez modal) ---
    // Musi być globalna (window.), aby drugi plik (list_edit) mógł jej użyć
    window.handleEditFormSubmit = async function(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton ? submitButton.textContent : 'Zapisz';
        
        if (submitButton) {
            submitButton.textContent = 'Zapisywanie...';
            submitButton.disabled = true;
        }

        let responseText = '';
        try {
            const formData = new FormData(form);
            const payload = new URLSearchParams(formData);

            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                     'Content-Type': 'application/x-www-form-urlencoded',
                     'X-Requested-With': 'XMLHttpRequest'
                },
                body: payload
            });

            responseText = await response.text();
            let result;
            let isSuccess = false;

            if (response.ok || response.redirected) {
                try {
                    result = JSON.parse(responseText);
                    if (result.status === 'success') isSuccess = true;
                    else throw new Error(result.message || 'Serwer zwrócił błąd w JSON.');
                } catch (e) {
                    console.warn("Odpowiedź serwera nie była JSONem sukcesu, ale status OK - zakładam sukces.");
                    isSuccess = true;
                }
            } else {
                 let errorMessage = `Błąd serwera (${response.status})`;
                 try { result = JSON.parse(responseText); errorMessage = result.message || errorMessage; } 
                 catch (e) { errorMessage = `${errorMessage}: ${responseText.substring(0, 150)}`; }
                 throw new Error(errorMessage);
            }

            if (isSuccess) {
                if (submitButton) submitButton.textContent = 'Zapisano!';
                setTimeout(() => {
                    if (window.calendar) window.calendar.refetchEvents();
                    hideAllModals(); // Zamknij modal po sukcesie
                }, 1000);
            }
        } catch (error) {
            console.error("BŁĄD ZAPISU w handleEditFormSubmit:", error);
            showConfirmation({
                title: 'Błąd Zapisu',
                body: `<p>Nie udało się zapisać zmian:</p><p><i>${error.message}</i></p>`,
                onOk: function() {}
            });
             if (submitButton) {
                 submitButton.textContent = originalButtonText;
                 submitButton.disabled = false;
             }
        }
    }

    // --- Inicjalizacja Kalendarza FullCalendar ---
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: window.innerWidth < 768 ? 'listMonth' : 'dayGridMonth',
      locale: 'pl',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,listMonth'
      },
      buttonText: { today: 'Dzisiaj', month: 'Miesiąc', week: 'Tydzień', list: 'Lista' },
      height: 'auto',
      fixedWeekCount: false,
      events: eventsUrl,
      
      eventClick: function(info) {
        info.jsEvent.preventDefault(); // Zawsze zapobiegaj domyślnej akcji
        // Logika kliknięcia jest teraz w pełni obsługiwana przez eventContent 
        // i dedykowane listenery w dashboard_list_edit.js dla widoku listy.
        // Poniżej obsługa kliknięcia dla widoków siatki (otwarcie modala).
        if (info.view.type !== 'listMonth') {
            const detailsUrl = detailsUrlTemplate.replace('0', info.event.id);
            window.showDetailsModalWithUrl(detailsUrl, info.event.title);
        }
      },

      eventContent: function(arg) {
          // Jeśli jesteśmy w widoku listy, wywołaj funkcję z drugiego pliku JS
          // Sprawdzamy, czy funkcja renderListItem istnieje, zanim ją wywołamy
          if (arg.view.type === 'listMonth' && typeof window.renderListItem === 'function') { 
              return window.renderListItem(arg, isAdmin);
          }
          
          // Logika dla widoków siatki (miesiąc, tydzień)
          let newIndicator = (arg.event.extendedProps && arg.event.extendedProps.is_new) ? '<span class="new-event-indicator"></span>' : '';
          return { html: '<div>' + newIndicator + arg.event.title + '</div>' };
      }
    });
    
    // Uczynienie obiektu kalendarza dostępnym globalnie dla drugiego pliku JS
    window.calendar = calendar; 
    
    // Renderuj kalendarz
    calendar.render();

    // --- Logika Przycisku "Wyczyść Miesiąc" ---
    const clearButton = document.getElementById('clearMonthBtn');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            const currentDate = calendar.getDate();
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth() + 1;
            const monthName = currentDate.toLocaleString('pl-PL', { month: 'long' });

            window.showConfirmation({
                title: 'Potwierdź usunięcie',
                body: '<p>Czy na pewno chcesz usunąć <strong>wszystkie</strong> niezarchiwizowane zlecenia z miesiąca: <strong>' + monthName + ' ' + year + '</strong>?</p>',
                onOk: function() {
                    fetch(clearMonthUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ year: year, month: month }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        window.showConfirmation({ title: data.status === 'success' ? 'Sukces' : 'Błąd', body: '<p>' + data.message + '</p>', onOk: function() {} });
                        if (data.status === 'success') calendar.refetchEvents();
                    })
                    .catch(error => {
                        console.error('Błąd podczas czyszczenia miesiąca:', error);
                        window.showConfirmation({ title: 'Błąd Sieciowy', body: '<p>Wystąpił błąd komunikacji.</p>', onOk: function() {} });
                    });
                }
            });
        });
    }

    // --- Delegacja zdarzeń dla formularzy edycji w OKNIE MODALNYM ---
    if (modalBody) {
        modalBody.addEventListener('submit', function(e) {
            const form = e.target;
            // Sprawdzamy, czy to na pewno formularz edycji w modalu
            if (form.method.toLowerCase() === 'post' && form.action.includes('/edit')) {
                e.preventDefault(); // ZATRZYMAJ PRZEŁADOWANIE STRONY
                
                // Sprawdź, czy funkcja zapisu (z dashboard_list_edit.js) jest dostępna
                if (typeof window.handleEditFormSubmit === 'function') {
                    window.handleEditFormSubmit(form); // Wywołaj funkcję zapisu
                } else {
                    // Ten błąd może się pojawić, jeśli list_edit.js się nie załaduje
                    console.error("BŁĄD KRYTYCZNY: Funkcja handleEditFormSubmit() nie jest załadowana!");
                    alert("Wystąpił błąd - brak funkcji zapisu.");
                }
            }
        });
    }

    console.log("Skrypt dashboard_main.js załadowany poprawnie.");
});

