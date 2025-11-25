// gitlab-proxy.js
const http = require("http");
const https = require("https");
const { URL } = require("url");

const targetUrl = new URL("https://gitlab.arubabank.com");

const server = http.createServer((req, res) => {
  const options = {
    hostname: targetUrl.hostname,
    port: 443,
    path: req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: "gitlab.arubabank.com", // backend hostname
    },
    rejectUnauthorized: false, // ⚠️ Insecure - only use in trusted environments
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

server.listen(8444, () => {
  console.log("✅ GitLab proxy running at http://localhost:8444");
});