// coder-proxy.js
const http = require("http");
const https = require("https");
const { URL } = require("url");

const targetUrl = new URL("https://127.0.0.1:443");

const server = http.createServer((req, res) => {
  const options = {
    hostname: targetUrl.hostname,
    port: targetUrl.port,
    path: req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: "coder.arubabank.com", // for backend to recognize host
    },
    rejectUnauthorized: false,
  };

  const proxyReq = https.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on("error", (err) => {
    console.error("Proxy error:", err.message);
    res.writeHead(502);
    res.end("Proxy failed: " + err.message);
  });

  req.pipe(proxyReq, { end: true });
});

server.listen(8443, () => {
  console.log("✅ Coder proxy running at http://localhost:8443");
});