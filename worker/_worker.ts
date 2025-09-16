export interface Env {
  OPENAI_KEY: string;
  OPENAI_BETA?: string;       // e.g. "realtime=v1"
  OPENAI_ORG_ID?: string;     // optional
  OPENAI_PROJECT?: string;    // optional
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    // Simple health check
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ ok: true, env: { OPENAI_KEY: !!env.OPENAI_KEY, OPENAI_BETA: env.OPENAI_BETA ?? null, OPENAI_ORG_ID: !!env.OPENAI_ORG_ID, OPENAI_PROJECT: !!env.OPENAI_PROJECT } }), {
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    // WebSocket gateway: /v1/realtime?model=...
    if (url.pathname.startsWith("/v1/realtime")) {
      if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
        return new Response("Expected WebSocket upgrade", {
          status: 426,
          headers: { "connection": "Upgrade", "upgrade": "websocket" }
        });
      }

      const model = url.searchParams.get("model") || "gpt-4o-realtime-preview-2024-12-17";
      const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

      // Connect from Worker -> OpenAI (upstream) as a WebSocket client
      const upstreamResp = await fetch(upstreamUrl, {
        headers: {
          "Authorization": `Bearer ${env.OPENAI_KEY}`,
          "OpenAI-Beta": env.OPENAI_BETA || "realtime=v1",
          ...(env.OPENAI_ORG_ID ? { "OpenAI-Organization": env.OPENAI_ORG_ID } : {}),
          ...(env.OPENAI_PROJECT ? { "OpenAI-Project": env.OPENAI_PROJECT } : {}),
          "Connection": "Upgrade",
          "Upgrade": "websocket",
        }
      });

      if (!upstreamResp.webSocket) {
        return new Response("Upstream WebSocket failed", { status: 502 });
      }
      const upstream = upstreamResp.webSocket;
      upstream.accept();

      // Create a pair: client <-> (CF Worker) <-> upstream
      // @ts-ignore
      const pair = new WebSocketPair();
      const client = pair[0];
      const server = pair[1];
      // @ts-ignore
      server.accept();

      // Pump data both ways
      server.addEventListener("message", (evt: MessageEvent) => upstream.send(evt.data));
      upstream.addEventListener("message", (evt: MessageEvent) => server.send(evt.data));

      server.addEventListener("close", (evt: CloseEvent) => upstream.close(evt.code, evt.reason));
      upstream.addEventListener("close", (evt: CloseEvent) => server.close(evt.code, evt.reason));

      server.addEventListener("error", () => upstream.close(1011, "cf-error"));
      upstream.addEventListener("error", () => server.close(1011, "upstream-error"));

      return new Response(null, { status: 101, webSocket: client });
    }

    return new Response("Not Found (realtime worker)", { status: 404 });
  }
};
