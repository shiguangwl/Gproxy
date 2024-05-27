(function() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(registration => console.log('Service Worker 注册成功:', registration))
            .catch(error => console.log('Service Worker 注册失败:', error));
    }

    // Helper function to get the modified URL
    function getModifiedUrl(url) {
        const parsedUrl = new URL(url, location.origin);
        return parsedUrl.origin === location.origin ? url : `${location.origin}/#global_proxy_path#/${parsedUrl.href}`;
    }

    // Hook for fetch
    const originalFetch = window.fetch;
    window.fetch = function(input, options) {
        const url = (typeof input === 'string') ? input : input.url;
        const modifiedUrl = getModifiedUrl(url);

        if (typeof input === 'string') {
            return originalFetch(modifiedUrl, options);
        } else {
            // FIXME: This is a temporary fix for Google Drive videos
            if (input.url.indexOf('googlevideo.com/videoplayback') !== -1) {
                const modifiedRequest = new Request(modifiedUrl, { ...input, url: modifiedUrl });
                return originalFetch(modifiedRequest, options);
            }else{
                const modifiedRequest = new Request(modifiedUrl, {
                    ...options, // Ensure all options are included
                    method: input.method, // Preserve the original method
                    headers: input.headers, // Preserve the original headers
                    body: input.body, // Preserve the original body
                    credentials: input.credentials, // Preserve credentials if any
                    cache: input.cache, // Preserve cache settings if any
                    mode: input.mode, // Preserve mode if any
                    redirect: input.redirect, // Preserve redirect settings if any
                    referrer: input.referrer, // Preserve referrer if any
                    referrerPolicy: input.referrerPolicy, // Preserve referrer policy if any
                    integrity: input.integrity, // Preserve integrity if any
                    keepalive: input.keepalive, // Preserve keepalive if any
                    signal: input.signal // Preserve signal if any
                });
                return originalFetch(modifiedRequest);
            }
        }
    };

    // Hook for XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        const modifiedUrl = getModifiedUrl(url);
        return originalOpen.call(this, method, modifiedUrl, async, user, password);
    };

})();
