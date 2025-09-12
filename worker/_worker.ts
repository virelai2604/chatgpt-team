export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
}
export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname !== "/v1/realtime") return new Response("Not Found", { status: 404 });
    if ((req.headers.get("Upgrade")||"").toLowerCase() !== "websocket") return new Response("Expected WebSocket upgrade", { status: 426 });

    // @ts-ignore Cloudflare runtime
    const pair = new WebSocketPair(); const [client, server] = Object.values(pair) as WebSocket[];
    // @ts-ignore
    server.accept();

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const hdrs = new Headers({ "Authorization": `Bearer ${env.OPENAI_KEY}`, "OpenAI-Beta": "realtime=v1" });
    if (env.OPENAI_ORG_ID) hdrs.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT)  hdrs.set("OpenAI-Project", env.OPENAI_PROJECT);

    const upstream = await fetch(`https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`, { headers: hdrs }) as any;
    const ws = upstream.webSocket as WebSocket | undefined;
    if (!ws) { server.close(1011, "Upstream unavailable"); return new Response("Failed to connect upstream", { status: 502 }); }
    // @ts-ignore
    ws.accept();

    server.addEventListener("message", e => { try { ws.send(e.data); } catch {} });
    ws.addEventListener("message", e => { try { server.send(e.data); } catch {} });
    server.addEventListener("close",  e => { try { ws.close(e.code, e.reason||"client closed"); } catch {} });
    ws.addEventListener("close",      e => { try { server.close(e.code, e.reason||"upstream closed"); } catch {} });
    server.addEventListener("error",  () => { try { ws.close(1011, "client error"); } catch {} });
    ws.addEventListener("error",      () => { try { server.close(1011, "upstream error"); } catch {} });

    const ping = setInterval(() => { try { server.send(JSON.stringify({type:"ping", t:Date.now()})); } catch { clearInterval(ping); } }, 30000);
    ctx.waitUntil(new Promise<void>(r => { const done = () => { clearInterval(ping); r(); }; server.addEventListener("close", done); ws.addEventListener("close", done); }));
    return new Response(null, { status: 101, webSocket: client });
  }
}
