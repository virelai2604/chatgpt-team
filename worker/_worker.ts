export default {
  async fetch(req: Request, env: any, ctx: ExecutionContext): Promise<Response> {
    const { pathname, search } = new URL(req.url);

    if (pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        headers: { "content-type": "application/json; charset=utf-8",
                   "cache-control": "no-store",
                   "access-control-allow-origin": "*" }
      });
    }

    if (pathname === "/v1/realtime") {
      const upgrade = req.headers.get("upgrade") || "";
      if (upgrade.toLowerCase() !== "websocket")
        return new Response("Expected WebSocket", { status: 426 });

      const pair = new WebSocketPair();
      const [client, server] = [pair[0], pair[1]];

      const clientProtocols = (req.headers.get("sec-websocket-protocol") || "")
        .split(",").map(s => s.trim()).filter(Boolean);
      const chosen = clientProtocols.find(p => p) || "oai-realtime";
      // @ts-ignore
      server.accept(chosen);

      const upstreamUrl = `wss://api.openai.com${pathname}${search}`;
      const upstreamHeaders: Record<string,string> = {
        "Authorization": `Bearer ${env.OPENAI_KEY}`,
        "OpenAI-Beta": env.OPENAI_BETA || "realtime=v1"
      };
      if (env.OPENAI_ORG_ID) upstreamHeaders["OpenAI-Organization"] = env.OPENAI_ORG_ID;
      if (env.OPENAI_PROJECT) upstreamHeaders["OpenAI-Project"] = env.OPENAI_PROJECT;

      const upstreamResp = await fetch(upstreamUrl, {
        headers: { "Upgrade": "websocket", "Connection": "Upgrade",
                   "Sec-WebSocket-Protocol": chosen, ...upstreamHeaders }
      });

      // @ts-ignore
      const upstreamSocket = upstreamResp.webSocket;
      if (!upstreamSocket) {
        server.close(1011, "Failed upstream");
        return new Response("Upstream failed", { status: 502 });
      }
      // @ts-ignore
      upstreamSocket.accept();

      // Bridge traffic
      // @ts-ignore
      server.addEventListener("message", (e: MessageEvent) => upstreamSocket.send(e.data));
      // @ts-ignore
      upstreamSocket.addEventListener("message", (e: MessageEvent) => server.send(e.data));
      server.addEventListener("close", () => upstreamSocket.close());
      upstreamSocket.addEventListener("close", () => server.close());
      server.addEventListener("error", () => upstreamSocket.close(1011, "client error"));
      upstreamSocket.addEventListener("error", () => server.close(1011, "upstream error"));

      return new Response(null, { status: 101, webSocket: client });
    }

    return new Response("Not Found", { status: 404 });
  }
} satisfies ExportedHandler;
