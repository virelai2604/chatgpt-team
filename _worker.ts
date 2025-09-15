export interface Env { OPENAI_KEY: string; }

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime worker)", { status: 404 });
    }
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Create server/client sockets for the **client** side
    // @ts-ignore
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    // Ensure we always negotiate a subprotocol (default to 'oai-realtime')
    const clientProto = (req.headers.get("Sec-WebSocket-Protocol") || "").trim();
    const subproto = clientProto || "oai-realtime";

    // Build upstream headers **including Upgrade: websocket** and the beta gate
    const hdrs = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": "realtime=v1",
      "Upgrade": "websocket",
      "Sec-WebSocket-Protocol": subproto
    });

    // Open the upstream WebSocket to OpenAI (Workers will expose response.webSocket)
    const upstreamResp = await fetch(upstreamUrl, { headers: hdrs });
    // @ts-ignore
    const upstream = (upstreamResp as any).webSocket as WebSocket | undefined;
    if (!upstream) {
      server.close(1011, "Upstream unavailable");
      return new Response("Failed to connect upstream", { status: 502 });
    }
    // @ts-ignore
    upstream.accept();

    // Bi-directional relay
    server.addEventListener("message", (ev: any) => { try { upstream.send(ev.data); } catch {} });
    upstream.addEventListener("message", (ev: any) => { try { server.send(ev.data); } catch {} });

    server.addEventListener("close", (ev: any) => { try { upstream.close(ev.code, ev.reason || "client closed"); } catch {} });
    upstream.addEventListener("close", (ev: any) => { try { server.close(ev.code, ev.reason || "upstream closed"); } catch {} });

    server.addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });
    upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // Keep-alive ping to keep client socket open
    const ping = setInterval(() => { try { server.send(JSON.stringify({ type: "ping", t: Date.now() })); } catch { clearInterval(ping); } }, 30000);

    // Hold worker open until either side closes
    ctx.waitUntil(new Promise<void>((resolve) => {
      const done = () => { clearInterval(ping); resolve(); };
      server.addEventListener("close", done);
      upstream.addEventListener("close", done);
    }));

    // Return a proper 101 to the client incl. the negotiated subprotocol
    const respHeaders = new Headers();
    respHeaders.set("Sec-WebSocket-Protocol", subproto);
    return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
  }
};
