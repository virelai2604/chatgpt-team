export interface Env {
  OPENAI_KEY: string;
  // No org/project in this policy
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    // Only handle /v1/realtime here
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime worker)", { status: 404 });
    }
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Accept client websocket
    // @ts-ignore - Cloudflare runtime
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    // Upstream URL to OpenAI Realtime (param model is forwarded)
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    // Build headers (ONLY OPENAI_KEY; no org/project). Always set realtime beta.
    const proto = req.headers.get("Sec-WebSocket-Protocol") ?? undefined;
    const hdrs = new Headers({
      "Upgrade": "websocket",
      "Authorization": `"Bearer ${env.OPENAI_KEY}`"
      "OpenAI-Beta": "realtime=v1"
    });
    if (proto) hdrs.set("Sec-WebSocket-Protocol", proto);

    // Connect upstream
    const upstreamResp = await fetch(upstreamUrl, { headers: hdrs });
    // @ts-ignore
    const upstream = (upstreamResp as any).webSocket as WebSocket | undefined;
    if (!upstream) {
      // @ts-ignore
      server.close(1011, "Upstream unavailable");
      return new Response("Failed to connect upstream", { status: 502 });
    }
    // @ts-ignore
    upstream.accept();

    // Bridge messages both ways
    server.addEventListener("message", (ev: MessageEvent) => { try { upstream.send(ev.data); } catch {} });
    upstream.addEventListener("message", (ev: MessageEvent) => { try { server.send(ev.data); } catch {} });

    // Mirror close/error
    server.addEventListener("close", (ev: CloseEvent) => { try { upstream.close(ev.code, ev.reason || "client closed"); } catch {} });
    upstream.addEventListener("close", (ev: CloseEvent) => { try { server.close(ev.code, ev.reason || "upstream closed"); } catch {} });
    server.addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });
    upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // Keep-alive ping
    const ping = setInterval(() => {
      try { server.send(JSON.stringify({ type: "ping", t: Date.now() })); } catch { clearInterval(ping); }
    }, 30000);

    ctx.waitUntil(new Promise<void>((resolve) => {
      const done = () => { clearInterval(ping); resolve(); };
      server.addEventListener("close", done);
      upstream.addEventListener("close", done);
    }));

    const respHeaders = new Headers();
    if (proto) respHeaders.set("Sec-WebSocket-Protocol", proto);
    return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
  }
};