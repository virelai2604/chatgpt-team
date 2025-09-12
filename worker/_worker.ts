export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // optional; we set realtime=v1 explicitly below
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Only handle /v1/realtime
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found", { status: 404 });
    }

    // Require WebSocket upgrade
    const isWs = (req.headers.get("Upgrade") || "").toLowerCase() === "websocket";
    if (!isWs) {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Accept the client socket
    // @ts-ignore
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    // Build upstream OpenAI Realtime URL
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    // Carry through subprotocol if provided
    const subproto = req.headers.get("Sec-WebSocket-Protocol") || undefined;

    // Open upstream connection (server → OpenAI)
    const headers = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      // Enable Realtime (and allow assistants v2 if you later route it here)
      "OpenAI-Beta": "realtime=v1",
    });
    if (env.OPENAI_ORG_ID) headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) headers.set("OpenAI-Project", env.OPENAI_PROJECT);
    if (subproto) headers.set("Sec-WebSocket-Protocol", subproto);

    const upstreamResp = await fetch(upstreamUrl, {
      headers,
      // Initiate a WS upgrade to OpenAI
      // Cloudflare Workers treats this as a WebSocket handshake when Upgrade headers are present.
      // @ts-ignore
      webSocket: new WebSocket(upstreamUrl),
    }).catch(() => null as any);

    // Fallback: explicit Upgrade if the above style isn't supported in your runtime
    let upstream: WebSocket | null = null;
    try {
      // @ts-ignore
      if (!upstreamResp || !upstreamResp.webSocket) {
        const resp = await fetch(upstreamUrl, {
          headers: new Headers([
            ["Authorization", `Bearer ${env.OPENAI_KEY}`],
            ["OpenAI-Beta", "realtime=v1"],
            ...(env.OPENAI_ORG_ID ? [["OpenAI-Organization", env.OPENAI_ORG_ID]] : []),
            ...(env.OPENAI_PROJECT ? [["OpenAI-Project", env.OPENAI_PROJECT]] : []),
            ...(subproto ? [["Sec-WebSocket-Protocol", subproto]] : []),
            ["Connection", "Upgrade"],
            ["Upgrade", "websocket"],
          ]),
        });
        // @ts-ignore
        upstream = resp.webSocket;
      } else {
        // @ts-ignore
        upstream = upstreamResp.webSocket;
      }
    } catch (e) {
      try { server.close(1011, "upstream connect failed"); } catch {}
      return new Response("Upstream connection failed", { status: 502 });
    }

    if (!upstream) {
      try { server.close(1011, "no upstream socket"); } catch {}
      return new Response("No upstream socket", { status: 502 });
    }

    // @ts-ignore
    upstream.accept();

    // Bridge: client → upstream
    // @ts-ignore
    server.addEventListener("message", (ev: MessageEvent) => {
      try { upstream!.send(ev.data); } catch {}
    });
    // Bridge: upstream → client
    // @ts-ignore
    upstream.addEventListener("message", (ev: MessageEvent) => {
      try { server.send(ev.data); } catch {}
    });

    // Mirror close & errors
    // @ts-ignore
    server.addEventListener("close", (ev: CloseEvent) => {
      try { upstream!.close(ev.code, ev.reason || "client closed"); } catch {}
    });
    // @ts-ignore
    upstream.addEventListener("close", (ev: CloseEvent) => {
      try { server.close(ev.code, ev.reason || "upstream closed"); } catch {}
    });
    // @ts-ignore
    server.addEventListener("error", () => {
      try { upstream!.close(1011, "client error"); } catch {}
    });
    // @ts-ignore
    upstream.addEventListener("error", () => {
      try { server.close(1011, "upstream error"); } catch {}
    });

    // Keepalive ping
    const ping = setInterval(() => {
      try { server.send(JSON.stringify({ type: "ping", t: Date.now() })); }
      catch { clearInterval(ping); }
    }, 30000);

    // Return 101 Switching Protocols with echoed subprotocol
    const respHdrs = new Headers();
    if (subproto) respHdrs.set("Sec-WebSocket-Protocol", subproto);
    // @ts-ignore
    return new Response(null, { status: 101, webSocket: client, headers: respHdrs });
  },
};