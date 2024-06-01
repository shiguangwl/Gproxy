(function() {
    // if ('serviceWorker' in navigator) {
    //     navigator.serviceWorker.register('/static/service-worker.js')
    //         .then(registration => console.log('Service Worker 注册成功:', registration))
    //         .catch(error => console.log('Service Worker 注册失败:', error));
    // }

    // Helper function to get the modified URL
    // 设置一个cookie
    // parental-control=yes
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/`;
    }
    setCookie('parental-control', 'yes', 9999);

    // Common js
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
            const modifiedRequest = new Request(modifiedUrl, {
                ...options,
                method: input.method,
                headers: input.headers,
                body: input.body,
                credentials: input.credentials,
                cache: input.cache,
                mode: input.mode,
                redirect: input.redirect,
                referrer: input.referrer,
                referrerPolicy: input.referrerPolicy,
                integrity: input.integrity,
                keepalive: input.keepalive,
                signal: input.signal
            });
            return originalFetch(modifiedRequest);
        }
    };

    // Hook for XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        const modifiedUrl = getModifiedUrl(url);
        return originalOpen.call(this, method, modifiedUrl, async, user, password);
    };

    // hook Img
    function hookImg() {
        const property = Object.getOwnPropertyDescriptor(Image.prototype, 'src');
        const nativeSet = property.set;

        function customiseSrcSet(url) {
            // TODO do something
            console.log('hookImg:', url);
            nativeSet.call(this, url);
        }
        Object.defineProperty(Image.prototype, 'src', {
            set: customiseSrcSet,
        });
    }
    hookImg()

    // hook Open
    function hookOpen() {
        const nativeOpen = window.open;
        window.open = function (url) {
            // TODO do something
            nativeOpen.call(this, url);
        };
    }
    hookOpen()
})();
