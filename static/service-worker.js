// Definiujemy nazwę i wersję pamięci podręcznej (cache)
// Zmiana wersji spowoduje aktualizację cache'a u użytkownika
const CACHE_NAME = 'grafik-firmowy-cache-v1';

// Lista plików, które tworzą "skorupę" aplikacji (App Shell)
// Te pliki zostaną zapisane w cache'u podczas instalacji
const urlsToCache = [
  '/',
  '/static/css/style.css',
  // Możesz dodać tutaj inne kluczowe zasoby, np. logo
];

// Instalacja Service Workera
self.addEventListener('install', event => {
  // Czekamy, aż wszystkie operacje instalacyjne się zakończą
  event.waitUntil(
    // Otwieramy naszą pamięć podręczną
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Otwarto pamięć podręczną (cache)');
        // Dodajemy wszystkie pliki App Shell do cache'a
        return cache.addAll(urlsToCache);
      })
  );
});

// Aktywacja Service Workera
self.addEventListener('activate', event => {
  // Ta sekcja czyści stare wersje pamięci podręcznej
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Usuwanie starej pamięci podręcznej:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Przechwytywanie żądań sieciowych (fetch)
self.addEventListener('fetch', event => {
  event.respondWith(
    // Sprawdzamy, czy żądany zasób jest już w naszej pamięci podręcznej
    caches.match(event.request)
      .then(response => {
        // Jeśli zasób jest w cache'u, zwracamy go
        if (response) {
          return response;
        }

        // Jeśli zasobu nie ma w cache'u, próbujemy pobrać go z sieci
        return fetch(event.request).then(
          response => {
            // Jeśli odpowiedź jest niepoprawna, nie zapisujemy jej w cache'u
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Klonujemy odpowiedź, ponieważ może być użyta tylko raz
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                // Zapisujemy nowo pobrany zasób w cache'u na przyszłość
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        );
      })
  );
});
