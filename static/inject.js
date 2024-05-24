(function() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(registration => console.log('Service Worker 注册成功:', registration))
            .catch(error => console.log('Service Worker 注册失败:', error));
    }

    // Helper function to get the modified URL
    function getModifiedUrl(url) {
        const parsedUrl = new URL(url, location.origin);
        return parsedUrl.origin === location.origin ? url : `${location.origin}/${config_loader.global_proxy_path}/${parsedUrl.href}`;
    }

    // Hook for fetch
    const originalFetch = window.fetch;
    window.fetch = function(input, options) {
        const url = (typeof input === 'string') ? input : input.url;
        const modifiedUrl = getModifiedUrl(url);

        if (typeof input === 'string') {
            return originalFetch(modifiedUrl, options);
        } else {
            const modifiedRequest = new Request(modifiedUrl, { ...input, url: modifiedUrl });
            return originalFetch(modifiedRequest, options);
        }
    };

    // Hook for XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        const modifiedUrl = getModifiedUrl(url);
        return originalOpen.call(this, method, modifiedUrl, async, user, password);
    };

})();
