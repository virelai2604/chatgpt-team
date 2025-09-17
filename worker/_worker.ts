export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // defaulted below to realtime=v1
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    // Health
    if (url.pathname === "/health-rt" || url.pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    if (url.pathname !== "/v1/realtime") return new Response("Not Found (realtime worker)", { status: 404 });
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") return new Response("Expected WebSocket upgrade", { status: 426 });

    // Cloudflare WS pair
    // @ts-ignore
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    // Upstream OpenAI Realtime
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const headers = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA && env.OPENAI_BETA.trim()) || "realtime=v1"
    });
    if (env.OPENAI_ORG_ID) headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) headers.set("OpenAI-Project", env.OPENAI_PROJECT);

    // Default subprotocol if client didn't send one; pass it upstream too
    const proto = req.headers.get("Sec-WebSocket-Protocol") || "oai-realtime";
    headers.set("Sec-WebSocket-Protocol", proto);

    // Connect upstream and bridge
    // @ts-ignore - CF runtime supports WebSocket(url, protocols, { headers })
    const upstream = new WebSocket(upstreamUrl, [proto], { headers } as any);

    upstream.addEventListener("message", (ev: MessageEvent) => server.send(ev.data));
    server  .addEventListener("message", (ev: MessageEvent) => upstream.send(ev.data));
    upstream.addEventListener("close", (ev: any) => server.close(ev.code, ev.reason || "upstream closed"));
    server  .addEventListener("close", (ev: any) => upstream.close(ev.code, ev.reason || "client closed"));
    upstream.addEventListener("error", () => server.close(1011, "upstream error"));
    server  .addEventListener("error", () => upstream.close(1011, "client error"));

    // Echo the negotiated subprotocol back to the client per spec
    const respHeaders = new Headers();
    respHeaders.set("Sec-WebSocket-Protocol", proto);
    return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
  }
};
