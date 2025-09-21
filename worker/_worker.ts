export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // ✅ WebSocket Handler - BIFL Safe
    if (url.pathname.startsWith("/v1/realtime")) {
      const upgradeHeader = request.headers.get("Upgrade");
      console.log("[WS] Incoming request for /v1/realtime");
      console.log("[WS] Upgrade header: " + upgradeHeader);

      if (upgradeHeader !== "websocket") {
        return new Response("Expected WebSocket", { status: 426 });
      }

      try {
        const pair = new WebSocketPair();
        const [client, server] = Object.values(pair);

        // Accept the WebSocket *before* any async work
        server.accept();

        server.addEventListener("message", (event) => {
          console.log("[WS] Message:", event.data);
          server.send(JSON.stringify({
            type: "echo",
            data: event.data
          }));
        });

        server.addEventListener("close", () => {
          console.log("[WS] Closed by client");
        });

        server.addEventListener("error", (err) => {
          console.error("[WS] Error:", err.message);
        });

        // ✅ Always return immediately
        return new Response(null, {
          status: 101,
          webSocket: client
        });

      } catch (err) {
        return new Response("WS Upgrade failed: " + err.message, { status: 500 });
      }
    }

    // ✅ Proxy fallback to Pages
    if (url.pathname.startsWith("/v1/")) {
      const proxyUrl = "https://chatgpt-team.pages.dev" + url.pathname + url.search;
      const method = request.method;

      const resp = await fetch(proxyUrl, {
        method,
        headers: request.headers,
        body: method !== "GET" && method !== "HEAD" ? request.body : undefined,
      });

      return new Response(resp.body, {
        status: resp.status,
        headers: resp.headers,
      });
    }

    return new Response("Not Found", { status: 404 });
  }
};
