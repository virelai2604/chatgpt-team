export interface Env {
  OPENAI_KEY: string;            // Secret
  OPENAI_BETA?: string;          // "realtime=v1"
  OPENAI_ORG_ID?: string;        // optional
  OPENAI_PROJECT?: string;       // optional
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Only handle the realtime path
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime)", { status: 404 });
    }

    // WebSocket handshake required
    const upgrade = (request.headers.get("Upgrade") || "").toLowerCase();
    if (upgrade !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Build upstream URL: keep /v1/realtime and query (model, voice, etc.)
    const upstream = new URL("https://api.openai.com" + url.pathname + url.search);

    // Create WS pair and accept the server side before proxying
    const [client, server] = Object.values(new WebSocketPair()) as [WebSocket, WebSocket];
    server.accept();

    // Required OpenAI headers for Realtime WS
    const h = new Headers();
    h.set("Authorization", `Bearer ${env.OPENAI_KEY}`);
    h.set("OpenAI-Beta", env.OPENAI_BETA || "realtime=v1"); // per Realtime docs
    if (env.OPENAI_ORG_ID) h.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) h.set("OpenAI-Project", env.OPENAI_PROJECT);
    // Tell CF we're upgrading this request to WS
    h.set("Connection", "Upgrade");
    h.set("Upgrade", "websocket");

    // Bridge our server socket to OpenAI’s socket
    const upstreamResp = await fetch(upstream, {
      headers: h,
      webSocket: server,
    });

    // If OpenAI didn’t accept (101), surface that error
    if (upstreamResp.status !== 101) {
      try { server.close(); } catch {}
      const body = await upstreamResp.text().catch(() => "");
      return new Response(`Upstream WS refused (${upstreamResp.status})\n${body}`, {
        status: 502,
        headers: { "content-type": "text/plain" },
      });
    }

    // Handshake OK — return the client side to the caller
    return new Response(null, { status: 101, webSocket: client });
  },
};
