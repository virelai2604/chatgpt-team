// [[worker]] _worker.ts
export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // expect 'realtime=v1'
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime)", { status: 404 });
    }
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Create client/server pair for the **client** side
    // @ts-ignore Cloudflare runtime type
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair) as [WebSocket, WebSocket];
    // @ts-ignore
    server.accept();

    // Build upstream URL and headers for OpenAI Realtime
    const model = url.searchParams.get("model") || "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const beta = (env.OPENAI_BETA && env.OPENAI_BETA.trim()) || "realtime=v1";
    const headers = new Headers({
      Authorization: `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": beta,
      Upgrade: "websocket"
    });
    if (env.OPENAI_ORG_ID)   headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT)  headers.set("OpenAI-Project",      env.OPENAI_PROJECT);

    // Preserve client subprotocol if provided; default to 'oai-realtime'
    const clientProto = (req.headers.get("Sec-WebSocket-Protocol") || "").trim();
    headers.set("Sec-WebSocket-Protocol", clientProto || "oai-realtime");

    // Dial the upstream WebSocket (Workers exposes response.webSocket)
    const upstreamResp = await fetch(upstreamUrl, { headers });
    // @ts-ignore
    const upstream = (upstreamResp as any).webSocket as WebSocket | undefined;
    if (!upstream) {
      try { server.send(JSON.stringify({ type: "error", error: { message: `Upstream refused WebSocket (status ${upstreamResp.status})` } })); } catch {}
      server.close(1011, "Upstream WebSocket unavailable");
      return new Response("Failed to connect upstream", { status: 502 });
    }
    // @ts-ignore
    upstream.accept();

    // Bi-directional relay
    server.addEventListener("message", (ev: MessageEvent) => { try { upstream.send(ev.data); } catch {} });
    upstream.addEventListener("message", (ev: MessageEvent) => { try { server.send(ev.data); } catch {} });

    server.addEventListener("close",  (ev: CloseEvent) => { try { upstream.close(ev.code, ev.reason || "client closed"); } catch {} });
    upstream.addEventListener("close",(ev: CloseEvent) => { try { server.close(ev.code, ev.reason || "upstream closed"); } catch {} });

    server.addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });
    upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // Keep-alive ping so the client socket doesn’t idle out
    const ping = setInterval(() => { try { server.send(JSON.stringify({ type: "ping", t: Date.now() })); } catch { clearInterval(ping); } }, 30000);
    ctx.waitUntil(new Promise<void>((resolve) => {
      const done = () => { clearInterval(ping); resolve(); };
      server.addEventListener("close", done);
      upstream.addEventListener("close", done);
    }));

    // Return 101 with client end
    return new Response(null, { status: 101, webSocket: client });
  },
};