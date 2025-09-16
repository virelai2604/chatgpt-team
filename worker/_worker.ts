export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // optional; defaulted below to realtime=v1
}

// Minimal WS relay for OpenAI Realtime
export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Health
    if (url.pathname === "/health-rt" || url.pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    if (url.pathname !== "/v1/realtime") {
      return new Response("Not Found", { status: 404 });
    }

    const upgrade = (req.headers.get("upgrade") || "").toLowerCase();
    if (upgrade !== "websocket") {
      return new Response(JSON.stringify({ ok: false, error: "expected websocket upgrade" }), {
        status: 426,
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    // @ts-ignore - Cloudflare runtime
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair) as WebSocket[];
    // @ts-ignore
    server.accept();

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const headers = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA && env.OPENAI_BETA.trim()) || "realtime=v1",
    });
    if (env.OPENAI_ORG_ID)  headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) headers.set("OpenAI-Project", env.OPENAI_PROJECT);

    const requested = (req.headers.get("Sec-WebSocket-Protocol") || "").split(",")[0]?.trim();
    const chosenProto = requested || "oai-realtime";

    const upstream = new WebSocket(upstreamUrl, chosenProto ? [chosenProto] : undefined, { headers } as any);

    // Bridge messages
    server.addEventListener("message", (ev: MessageEvent) => upstream.send(ev.data));
    upstream.addEventListener("message", (ev: MessageEvent) => server.send(ev.data));

    upstream.addEventListener("close", () => server.close(1000, "upstream closed"));
    server  .addEventListener("close", () => upstream.close(1000, "client closed"));
    upstream.addEventListener("error", () => server.close(1011, "upstream error"));
    server  .addEventListener("error", () => upstream.close(1011, "client error"));

    // 101 with echoed subprotocol per the spec
    return new Response(null, {
      status: 101,
      webSocket: client,
      headers: new Headers({ "Sec-WebSocket-Protocol": chosenProto })
    });
  }
};
