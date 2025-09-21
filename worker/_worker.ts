export default {
  async fetch(req: Request, env: any): Promise<Response> {
    const { pathname, search } = new URL(req.url);

    if (pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime", ts: Date.now() }), {
        headers: {
          "content-type": "application/json; charset=utf-8",
          "cache-control": "no-store",
          "access-control-allow-origin": "*"
        }
      });
    }

    if (pathname === "/v1/realtime") {
      const upgrade = req.headers.get("upgrade") || "";
      if (upgrade.toLowerCase() !== "websocket") return new Response("Expected WebSocket", { status: 426 });

      const pair = new WebSocketPair();
      const [client, server] = [pair[0], pair[1]];
      const protocols = (req.headers.get("sec-websocket-protocol") || "").split(",").map(p => p.trim()).filter(Boolean);
      const chosen = protocols.find(p => p) || "oai-realtime";
      // @ts-ignore
      server.accept(chosen);

      const upstreamUrl = `wss://api.openai.com${pathname}${search}`;
      const headers: Record<string,string> = {
        "Authorization": `Bearer ${env.OPENAI_KEY}`,
        "OpenAI-Beta": env.OPENAI_BETA || "realtime=v1"
      };
      if (env.OPENAI_ORG_ID) headers["OpenAI-Organization"] = env.OPENAI_ORG_ID;
      if (env.OPENAI_PROJECT) headers["OpenAI-Project"] = env.OPENAI_PROJECT;

      const upstreamResp = await fetch(upstreamUrl, {
        headers: { "Upgrade": "websocket", "Connection": "Upgrade", "Sec-WebSocket-Protocol": chosen, ...headers }
      });

      // @ts-ignore
      const upstream = upstreamResp.webSocket;
      if (!upstream) { server.close(1011, "Upstream failed"); return new Response("Upstream failed", { status: 502 }); }
      // @ts-ignore
      upstream.accept();

      // Pipe
      // @ts-ignore
      server.addEventListener("message", (e: MessageEvent) => upstream.send(e.data));
      // @ts-ignore
      upstream.addEventListener("message", (e: MessageEvent) => server.send(e.data));
      server.addEventListener("close", () => upstream.close());
      upstream.addEventListener("close", () => server.close());

      return new Response(null, { status: 101, webSocket: client });
    }

    return new Response("Not Found", { status: 404 });
  }
} satisfies ExportedHandler;
