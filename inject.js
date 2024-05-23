(function () {
    // Hook for fetch
    const originalFetch = window.fetch;
    window.fetch = function (url, options) {
        const modifiedUrl = location.origin + '/proxy/' + btoa(url);
        return originalFetch(modifiedUrl, options);
    };
    // Hook for XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, async, user, password) {
        const modifiedUrl = location.origin + '/proxy/' + btoa(url);
        return originalOpen.call(this, method, modifiedUrl, async, user, password);
    };
})();
