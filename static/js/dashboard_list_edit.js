/**
 * Logika specyficzna dla widoku listy w panelu głównym (dashboard).
 * Odpowiada TYLKO za renderowanie elementów listy i rozwijanie szczegółów (podgląd).
 */

(function() { // Używamy IIFE dla lepszej izolacji kodu

    /**
     * Renderuje pojedynczy element listy FullCalendar na podstawie szablonu HTML.
     * Wyświetla tylko podstawowe informacje (godziny, kilometry).
     * @param {object} arg - Argumenty zdarzenia dostarczone przez FullCalendar.
     * @param {boolean} isAdmin - Czy zalogowany użytkownik jest administratorem/kierownikiem (nieużywane w tej wersji).
     * @returns {object} Obiekt zawierający węzły DOM elementu listy.
     */
    window.renderListItem = function(arg, isAdmin) { // isAdmin jest teraz ignorowany w renderowaniu
        const listItemTemplate = document.getElementById('list-item-template');
        if (!listItemTemplate) {
            console.error("Błąd krytyczny: Nie znaleziono szablonu #list-item-template!");
            return { html: 'Błąd szablonu' };
        }
        try {
            const templateContent = listItemTemplate.content.cloneNode(true);
            const container = templateContent.querySelector('.list-item-container');
            if (!container) {
                 console.error("Błąd krytyczny: Brak .list-item-container w szablonie!");
                 return { html: 'Błąd struktury szablonu' };
            }

            const props = arg.event.extendedProps || {};
            const eventId = arg.event.id;
            
            container.dataset.tripId = eventId;

            // Wypełnianie danych ogólnych
            const link = container.querySelector('.list-item-link');
            const titleText = container.querySelector('.list-item-title-text');
            const indicator = container.querySelector('.new-event-indicator');
            if (link) link.href = arg.event.url;
            if (titleText) titleText.textContent = arg.event.title;
            if (indicator && props.is_new) indicator.style.display = 'inline-block';

            // Wypełnianie widoku tylko do odczytu
            const workStartTimeEl = container.querySelector('.work-start-time');
            const workEndTimeEl = container.querySelector('.work-end-time');
            const kilometersEl = container.querySelector('.kilometers');

            if (workStartTimeEl) workStartTimeEl.textContent = props.work_start_time || 'N/A';
            if (workEndTimeEl) workEndTimeEl.textContent = props.work_end_time || 'N/A';
            const kmValue = (props.kilometers !== '' && props.kilometers !== null && props.kilometers !== undefined) ? String(props.kilometers) : 'N/A';
            if (kilometersEl) kilometersEl.textContent = kmValue;
            
            // Usunięto całą logikę konfiguracji formularza edycyjnego

            return { domNodes: [container] }; // Zwracamy tylko główny kontener
        } catch (error) {
            console.error("Błąd w renderListItem:", error, arg);
            return { html: 'Błąd renderowania' };
        }
    }

    // Usunięto całą funkcję `handleEditFormSubmit`, ponieważ edycja w liście jest wyłączona

    // --- Event Listenery ---
    document.addEventListener('DOMContentLoaded', function() {
        const calendarEl = document.getElementById('calendar');
        if (!calendarEl) {
             console.log("Element #calendar nie znaleziony, event listenery list_edit nie zostaną dodane.");
             return;
        }

        // Używamy delegacji zdarzeń na KONTENERZE KALENDARZA
        calendarEl.addEventListener('click', function(e) {
            // --- Obsługa przycisku rozwijania (strzałki) ---
            const toggle = e.target.closest('.details-toggle');
            if (toggle) {
                e.preventDefault();
                toggle.classList.toggle('active');
                // Znajdź panel szczegółów POWYŻEJ przycisku w strukturze DOM
                const details = toggle.closest('.list-item-container')?.querySelector('.list-event-details');
                if (details) {
                    // Przełącz widoczność panelu
                    details.style.display = details.style.display === 'block' ? 'none' : 'block';
                }
            }

            // --- Obsługa kliknięcia na tytuł w widoku listy ---
            const link = e.target.closest('.list-item-link');
            if (link && window.calendar && window.calendar.view.type === 'listMonth') {
                 e.preventDefault();
                 // Znajdź przycisk strzałki dla tego samego elementu i zasymuluj kliknięcie
                 const toggleButton = link.closest('.fc-list-item-title')?.querySelector('.details-toggle');
                 if(toggleButton) {
                     toggleButton.click();
                 }
            }
        });

        // Usunięto listener dla zdarzenia 'submit', ponieważ nie ma formularza edycji w liście

        console.log("Skrypt dashboard_list_edit.js załadowany (tylko podgląd).");
    });

})(); // Koniec IIFE


