// AutoHire Service Worker for Web Push Notifications & Background Waitlist Events
const CACHE_NAME = 'autohire-sw-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Handle Background Push Event
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
    icon: 'background.png.jpeg',
    badge: 'background.png.jpeg',
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

// Handle Notification Click Action
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
