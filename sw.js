// AutoHire Service Worker: Offline Cache Engine & Web Push Notifications
const CACHE_NAME = 'autohire-pwa-v4';
const STATIC_ASSETS = [
  '/',
  'index.html',
  'chatbot.html',
  'analyzer.html',
  'dashboard.html',
  'profile.html',
  'sign-in.html',
  'register.html',
  'getstarted.html',
  'api-config.js',
  'waitlist-system.js',
  'manifest.json',
  'icon-192.svg',
  'icon-512.svg'
];

// Install Event: Cache Core Static Resources
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('PWA Asset caching notice:', err);
      });
    })
  );
});

// Activate Event: Cleanup Old Caches Immediately & Claim Clients
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Interceptor: Network-First for API and HTML/CSS/JS, Fallback to Cache
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Ignore non-GET requests
  if (request.method !== 'GET') return;

  // Strategy 1: Network-First for API endpoints
  if (url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) return cachedResponse;
            return new Response(JSON.stringify({ error: 'Offline mode active', jobs: [] }), {
              headers: { 'Content-Type': 'application/json' }
            });
          });
        })
    );
    return;
  }

  // Strategy 2: Network-First for HTML/CSS/JS with Cache Fallback
  event.respondWith(
    fetch(request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const copy = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          if (request.headers.get('accept') && request.headers.get('accept').includes('text/html')) {
            return caches.match('index.html');
          }
        });
      })
  );
});

// Web Push Notification Handler
self.addEventListener('push', (event) => {
  let data = {
    title: 'A spot opened up!',
    body: 'A position you are waiting for has a free slot. Apply now!',
    jobId: 'default',
    url: 'chatbot.html'
  };

  if (event.data) {
    try {
      data = Object.assign(data, event.data.json());
    } catch (e) {
      data.body = event.data.text() || data.body;
    }
  }

  const options = {
    body: data.body,
    icon: 'icon-192.svg',
    badge: 'icon-192.svg',
    data: {
      url: data.url || 'chatbot.html',
      jobId: data.jobId
    },
    actions: [
      { action: 'apply', title: '🚀 Apply Now' },
      { action: 'close', title: 'Close' }
    ],
    vibrate: [200, 100, 200],
    tag: `waitlist-${data.jobId || Date.now()}`,
    renotify: true
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification Click Handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : 'chatbot.html';

  if (event.action === 'apply' || !event.action) {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes(targetUrl) && 'focus' in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
    );
  }
});
