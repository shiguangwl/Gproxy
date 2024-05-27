// self.addEventListener('install', (event) => {
//     // 跳过等待，立即激活 Service Worker
//     self.skipWaiting();
//     console.log('Service Worker installing.');
// });
//
// self.addEventListener('activate', (event) => {
//     console.log('Service Worker activated.');
// });
//
// self.addEventListener('fetch', (event) => {
//     console.log('Fetching:', event.request.url);
//     // 可以在这里添加自定义的响应逻辑，例如缓存策略等
//     event.respondWith(
//         fetch(event.request).then((response) => {
//             // 这里可以处理响应，例如将其存入缓存
//             return response;
//         }).catch((error) => {
//             // 处理错误，例如返回一个离线页面
//             return new Response('网络请求失败，请检查您的网络连接。');
//         })
//     );
// });
