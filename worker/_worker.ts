export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;

    if (pathname === "/v1/realtime" && request.headers.get("Upgrade")?.toLowerCase() === "websocket") {
      const pair = new WebSocketPair();
      const client = pair[0], server = pair[1];
      server.accept();

      handleUpstreamRelay(request, url, server).catch((err) =>
        console.error("Relay failed:", err)
      );

      return new Response(null, { status: 101, webSocket: client });
    }

    // Fallback proxy to Pages root domain
    const upstreamUrl = "https://chatgpt-team.pages.dev" + url.pathname + url.search;
    return fetch(upstreamUrl, {
      method: request.method,
      headers: request.headers,
      body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined
    });
  }
};

async function handleUpstreamRelay(request: Request, url: URL, server: WebSocket) {
  const upstreamResp = await fetch("https://api.openai.com/v1/realtime" + url.search, {
    method: "GET",
    headers: {
      "Authorization": request.headers.get("Authorization") ?? "",
      "OpenAI-Organization": request.headers.get("OpenAI-Org") ?? "",
      "OpenAI-Beta": request.headers.get("OpenAI-Beta") ?? "realtime=v1",
      "Connection": "Upgrade",
      "Upgrade": "websocket",
      "Sec-WebSocket-Protocol": request.headers.get("Sec-WebSocket-Protocol") ?? ""
    },
  });

  const upstream = upstreamResp.webSocket;
  if (!upstream) {
    server.close(1011, "Upstream rejected");
    return;
  }

  upstream.accept();
  upstream.addEventListener("message", (e) => server.send(e.data));
  server.addEventListener("message", (e) => upstream.send(e.data));
  upstream.addEventListener("close", () => server.close());
  upstream.addEventListener("error", () => server.close(1011, "upstream error"));
  server.addEventListener("close", () => upstream.close());
  server.addEventListener("error", () => upstream.close(1011, "client error"));
}
