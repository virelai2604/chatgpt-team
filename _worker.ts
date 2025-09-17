export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // optional; defaulted below to realtime=v1
}

// Minimal WebSocket relay for OpenAI Realtime
export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Health check
    if (url.pathname === "/health-rt" || url.pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    if (url.pathname !== "/v1/realtime") {
      return new Response("Not found", { status: 404, headers: { "access-control-allow-origin": "*" } });
    }

    if (req.headers.get("Upgrade") !== "websocket") {
      return new Response("Expected WebSocket 'Upgrade' request.", { status: 426, headers: { "access-control-allow-origin": "*" }});
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair) as [WebSocket, WebSocket];

    // Accept our end
    // @ts-ignore - Cloudflare runtime
    server.accept();

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const requestedProto = (req.headers.get("Sec-WebSocket-Protocol") || "").split(",")[0]?.trim();
    const echoProto = requestedProto && requestedProto.length > 0 ? requestedProto : null;
    const headers = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA && env.OPENAI_BETA.trim()) || "realtime=v1",
    });
    if (env.OPENAI_ORG_ID)  headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) headers.set("OpenAI-Project", env.OPENAI_PROJECT);

    // Connect to OpenAI upstream; if client did not offer a subprotocol, default to 'oai-realtime' upstream
    const upstreamProtocols = echoProto ? [echoProto] : ["oai-realtime"];
    // @ts-ignore - Cloudflare runtime allows 'headers' option here
    const upstream = new WebSocket(upstreamUrl, upstreamProtocols, { headers } as any);

    // Bridge messages bi-directionally
    server.addEventListener("message", (ev: MessageEvent) => upstream.send(ev.data));
    upstream.addEventListener("message", (ev: MessageEvent) => server.send(ev.data));

    upstream.addEventListener("close", () => server.close(1000, "upstream closed"));
    server .addEventListener("close", () => upstream.close(1000, "client closed"));
    upstream.addEventListener("error", () => server.close(1011, "upstream error"));
    server .addEventListener("error", () => upstream.close(1011, "client error"));

    const respHeaders = new Headers();
    if (echoProto) respHeaders.set("Sec-WebSocket-Protocol", echoProto);

    // Return 101 Switching Protocols
    return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
  }
} satisfies ExportedHandler<Env>;
