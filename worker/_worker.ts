export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // default set below to realtime=v1
}

export default {
  async fetch(req: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    // HTTP health for quick checks
    if (url.pathname === "/health-rt" || url.pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    // Serve only the WS endpoint
    if (url.pathname !== "/v1/realtime") {
      return new Response("Not Found (realtime worker)", { status: 404 });
    }

    // Require WebSocket upgrade
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Cloudflare WS pair
    // @ts-ignore Cloudflare runtime
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    // Upstream OpenAI Realtime WS
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const headers = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA && env.OPENAI_BETA.trim()) || "realtime=v1"
    });
    if (env.OPENAI_ORG_ID)  headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) headers.set("OpenAI-Project",      env.OPENAI_PROJECT);

    // Preserve subprotocol (OpenAI suggests "oai-realtime" for event schema)
    const proto = req.headers.get("Sec-WebSocket-Protocol");
    const upstream = new WebSocket(upstreamUrl, proto ? [proto] : [], { headers } as any);

    // Bridge frames both directions
    upstream.addEventListener("message", (ev: MessageEvent) => server.send(ev.data));
    server  .addEventListener("message", (ev: MessageEvent) => upstream.send(ev.data));
    upstream.addEventListener("close", () => server.close());
    server  .addEventListener("close", () => upstream.close());
    upstream.addEventListener("error", () => server.close());
    server  .addEventListener("error", () => upstream.close());

    // Hand back the client socket
    return new Response(null, { status: 101, webSocket: client });
  }
};
