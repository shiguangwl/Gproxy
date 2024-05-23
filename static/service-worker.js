self.addEventListener('install', function(event) {
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function(event) {
    const url = new URL(event.request.url);
    console.log('拦截到请求:' + url)
    event.respondWith(fetch(event.request));
});
