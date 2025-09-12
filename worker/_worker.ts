export interface Env { OPENAI_KEY: string; OPENAI_ORG_ID?: string; OPENAI_PROJECT?: string; }
export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname !== "/v1/realtime") return new Response("Not Found", { status: 404 });
    if ((req.headers.get("Upgrade")||"").toLowerCase() !== "websocket") return new Response("Expected WebSocket upgrade", { status: 426 });

    // @ts-ignore
    const pair = new WebSocketPair(); const [client, server] = Object.values(pair) as WebSocket[];
    // @ts-ignore
    server.accept();

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const hdrs = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": "realtime=v1" // <- explicit here; remove if you switch to env.OPENAI_BETA
    });
    if (env.OPENAI_ORG_ID) hdrs.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) hdrs.set("OpenAI-Project", env.OPENAI_PROJECT);

    const upstreamResp = await fetch(`https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`, { headers: hdrs });
    // @ts-ignore
    const upstream = (upstreamResp as any).webSocket as WebSocket | undefined;
    if (!upstream) { server.close(1011, "Upstream unavailable"); return new Response("Failed to connect upstream", { status: 502 }); }
    // @ts-ignore
    upstream.accept();

    server.addEventListener("message", e => { try { upstream.send(e.data); } catch {} });
    upstream.addEventListener("message", e => { try { server.send(e.data); } catch {} });

    server.addEventListener("close",  e => { try { upstream.close(e.code, e.reason||"client closed"); } catch {} });
    upstream.addEventListener("close",e => { try { server.close(e.code, e.reason||"upstream closed"); } catch {} });

    server.addEventListener("error",  () => { try { upstream.close(1011, "client error"); } catch {} });
    upstream.addEventListener("error",() => { try { server.close(1011, "upstream error"); } catch {} });

    // @ts-ignore
    return new Response(null, { status: 101, webSocket: client });
  }
}
