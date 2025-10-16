const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
    app.use(
        ['/api'],
        createProxyMiddleware({
            target: 'https://localhost:5000', // ← 인증서 CN에 맞춰 'localhost' 권장
            changeOrigin: true,
            secure: false, // 개발용 자가서명 인증서 허용
            onProxyRes(proxyRes) {              // 혹시 백엔드가 절대URL로 리다이렉트하면 제거
                if (proxyRes.headers.location?.startsWith('https://127.0.0.1:5000')) {
                proxyRes.headers.location = proxyRes.headers.location.replace('https://127.0.0.1:5000', '');
                }
            }
        })
    );
};