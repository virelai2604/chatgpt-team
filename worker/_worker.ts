export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // e.g. "realtime=v1"
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    // lightweight health for WS worker
    if (url.pathname === "/v1/health-rt" || url.pathname === "/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        status: 200,
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    // enforce /v1/realtime + websocket upgrade
    if (url.pathname !== "/v1/realtime")
      return new Response("Not Found (realtime worker)", { status: 404 });
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // downstream socket pair for the client
    // @ts-ignore Cloudflare runtime
    const pair = new WebSocketPair();
    // @ts-ignore Cloudflare runtime
    const [client, server] = Object.values(pair);
    // @ts-ignore Cloudflare runtime
    server.accept();

    // model (keep client ?model=…)
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    // choose beta: env or safe fallback
    const beta = (env.OPENAI_BETA && env.OPENAI_BETA.trim()) ? env.OPENAI_BETA : "realtime=v1";

    // build upstream headers
    const h = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": beta,
      "Upgrade": "websocket"
    });
    if (env.OPENAI_ORG_ID)   h.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT)  h.set("OpenAI-Project",      env.OPENAI_PROJECT);

    // preserve client subprotocol if any
    const proto = (req.headers.get("Sec-WebSocket-Protocol") || "").trim();
    if (proto) h.set("Sec-WebSocket-Protocol", proto);

    // connect to OpenAI (Workers exposes response.webSocket on success)
    const upstreamResp = await fetch(upstreamUrl, { headers: h });
    // @ts-ignore Cloudflare runtime
    const upstream = (upstreamResp as any).webSocket as WebSocket | undefined;
    if (!upstream) {
      server.close(1011, "Upstream unavailable");
      return new Response("Failed to connect upstream", { status: 502 });
    }
    // @ts-ignore Cloudflare runtime
    upstream.accept();

    // bridge messages in both directions
    server.addEventListener("message", (ev: MessageEvent) => { try { upstream.send(ev.data); } catch {} });
    upstream.addEventListener("message", (ev: MessageEvent) => { try { server.send(ev.data); } catch {} });
    server.addEventListener("close",  (ev: CloseEvent) => { try { upstream.close(ev.code, ev.reason || "client closed"); } catch {} });
    upstream.addEventListener("close",(ev: CloseEvent) => { try { server.close(ev.code, ev.reason || "upstream closed"); } catch {} });
    server.addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });
    upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // keep-alive ping
    const ping = setInterval(() => { try { server.send(JSON.stringify({ type: "ping", t: Date.now() })); } catch { clearInterval(ping); } }, 30000);
    ctx.waitUntil(new Promise<void>((resolve) => {
      const done = () => { clearInterval(ping); resolve(); };
      server.addEventListener("close", done);
      upstream.addEventListener("close", done);
    }));

    // return 101 with the client socket (preserve protocol)
    const rh = new Headers();
    if (proto) rh.set("Sec-WebSocket-Protocol", proto);
    return new Response(null, { status: 101, webSocket: client, headers: rh });
  }
};