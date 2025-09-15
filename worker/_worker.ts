export interface Env { OPENAI_KEY: string; }

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/v1/realtime")) return new Response("Not Found (realtime worker)", { status: 404 });
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") return new Response("Expected WebSocket upgrade", { status: 426 });

    // @ts-ignore
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    // Build upstream headers
    const hdrs = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": "realtime=v1",
      "Upgrade": "websocket"             // <— REQUIRED for outgoing WS
    });

    // If client requested a subprotocol, forward it; else default to oai-realtime
    const proto = req.headers.get("Sec-WebSocket-Protocol") || "oai-realtime";
    hdrs.set("Sec-WebSocket-Protocol", proto);

    // Dial upstream; Workers runtime exposes `response.webSocket` on success
    const upstreamResp = await fetch(upstreamUrl, { headers: hdrs });
    // @ts-ignore
    const upstream = (upstreamResp as any).webSocket as WebSocket | undefined;
    if (!upstream) { server.close(1011, "Upstream unavailable"); return new Response("Failed to connect upstream", { status: 502 }); }
    // @ts-ignore
    upstream.accept();

    // Bridge frames both ways
    server.addEventListener("message", (ev: any) => { try { upstream.send(ev.data); } catch {} });
    upstream.addEventListener("message", (ev: any) => { try { server.send(ev.data); } catch {} });
    server.addEventListener("close",  (ev: any) => { try { upstream.close(ev.code, ev.reason || "client closed"); } catch {} });
    upstream.addEventListener("close",(ev: any) => { try { server.close(ev.code, ev.reason || "upstream closed"); } catch {} });
    server.addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });
    upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // Keep-alive ping
    const ping = setInterval(() => { try { server.send(JSON.stringify({ type: "ping", t: Date.now() })); } catch { clearInterval(ping); } }, 30000);
    ctx.waitUntil(new Promise<void>((resolve) => {
      const done = () => { clearInterval(ping); resolve(); };
      server.addEventListener("close", done);
      upstream.addEventListener("close", done);
    }));

    // Return the client half
    const respHeaders = new Headers();
    if (proto) respHeaders.set("Sec-WebSocket-Protocol", proto);
    return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
  }
};
