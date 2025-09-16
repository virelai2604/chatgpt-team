export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // defaulted below
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Scope: only /v1/realtime
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not found", { status: 404 });
    }

    // Require WebSocket upgrade
    const upgrade = request.headers.get("Upgrade");
    if (!upgrade || upgrade.toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket", { status: 426 });
    }

    // Accept client socket
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair) as [WebSocket, WebSocket];
    server.accept();

    // Build upstream request
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const headers = new Headers({
      "Upgrade": "websocket",
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA && env.OPENAI_BETA.trim()) || "realtime=v1",
    });
    if (env.OPENAI_ORG_ID)  headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) headers.set("OpenAI-Project",      env.OPENAI_PROJECT);

    // Preserve negotiated subprotocol (optional)
    const proto = request.headers.get("Sec-WebSocket-Protocol");
    if (proto) headers.set("Sec-WebSocket-Protocol", proto);

    // Connect upstream (Workers supports fetch+Upgrade for outbound WS)
    const resp = await fetch(upstreamUrl, { headers });
    const upstream = (resp as any).webSocket as WebSocket | undefined;
    if (!upstream) {
      server.close(1011, "Upstream failed");
      return new Response("Upstream failed", { status: 502 });
    }
    upstream.accept();

    // Bridge frames both directions
    server.addEventListener("message", (e) => upstream.send(e.data));
    upstream.addEventListener("message", (e) => server.send(e.data));
    server.addEventListener("close",   () => upstream.close());
    upstream.addEventListener("close", () => server.close());
    server.addEventListener("error",   () => upstream.close());
    upstream.addEventListener("error", () => server.close());

    // Return the client socket
    return new Response(null, { status: 101, webSocket: client });
  }
};