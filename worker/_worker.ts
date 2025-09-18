export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // default "realtime=v1"
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const { pathname, search } = new URL(req.url);

    // Simple health
    if (pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "access-control-allow-origin": "*" }
      });
    }

    if (pathname !== "/v1/realtime") return new Response("Not Found", { status: 404 });

    // Require WebSocket
    if ((req.headers.get("upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket", { status: 426 });
    }

    // @ts-ignore
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    const clientProto = (req.headers.get("sec-websocket-protocol") || "").split(",").map(s => s.trim()).find(Boolean) || "oai-realtime";
    // @ts-ignore
    server.accept(clientProto);

    // Query param model (default can be updated over time)
    const url = new URL(req.url);
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";

    // Upstream WSS to OpenAI Realtime
    const upstreamUrl = `wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;
    const headers: Record<string, string> = {
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA?.trim() || "realtime=v1"),
      "Upgrade": "websocket",
      "Connection": "Upgrade",
      "Sec-WebSocket-Protocol": clientProto
    };
    if (env.OPENAI_ORG_ID) headers["OpenAI-Organization"] = env.OPENAI_ORG_ID;
    if (env.OPENAI_PROJECT) headers["OpenAI-Project"] = env.OPENAI_PROJECT;

    const resp = await fetch(upstreamUrl, { headers });
    // @ts-ignore
    const upstream = resp.webSocket as WebSocket | undefined;
    if (!upstream) {
      const txt = await resp.text().catch(() => "");
      server.close(1011, "Upstream not available");
      return new Response("Failed to connect upstream: " + resp.status + " " + txt, { status: 502 });
    }
    // @ts-ignore
    upstream.accept(clientProto);

    // Bi-directional pipe
    // @ts-ignore
    server.addEventListener("message", (e: MessageEvent) => upstream.send(e.data));
    // @ts-ignore
    upstream.addEventListener("message", (e: MessageEvent) => server.send(e.data));

    server.addEventListener("close",   (e: any) => upstream.close(e.code, e.reason || "client closed"));
    upstream.addEventListener("close", (e: any) => server.close(e.code, e.reason || "upstream closed"));

    server.addEventListener("error",   () => upstream.close(1011, "client error"));
    upstream.addEventListener("error", () => server.close(1011, "upstream error"));

    return new Response(null, { status: 101, webSocket: client, headers: new Headers({ "Sec-WebSocket-Protocol": clientProto }) });
  }
} satisfies ExportedHandler<Env>;
