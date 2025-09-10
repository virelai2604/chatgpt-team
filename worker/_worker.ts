export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/v1/realtime") {
      // Reject plain GETs to avoid “hung code”
      if (req.headers.get("Upgrade")?.toLowerCase() !== "websocket") {
        return new Response("Expected WebSocket upgrade", { status: 426 });
      }

      // Accept client websocket
      const pair = new WebSocketPair();
      const [client, server] = Object.values(pair);
      server.accept();

      // Build upstream URL and headers
      const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
      const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;
      const proto = req.headers.get("Sec-WebSocket-Protocol") ?? undefined;
      const hdrs = new Headers({
        "Upgrade": "websocket",
        "Authorization": `Bearer ${env.OPENAI_KEY}`,
        "OpenAI-Beta": "realtime=v1"
      });
      if (proto) hdrs.set("Sec-WebSocket-Protocol", proto);
      if (env.OPENAI_ORG_ID) hdrs.set("OpenAI-Organization", env.OPENAI_ORG_ID);
      if (env.OPENAI_PROJECT) hdrs.set("OpenAI-Project", env.OPENAI_PROJECT);

      // Connect upstream
      const upstreamResp = await fetch(upstreamUrl, { headers: hdrs });
      const upstream = (upstreamResp as any).webSocket as WebSocket | undefined;
      if (!upstream) {
        server.close(1011, "Upstream unavailable");
        return new Response("Failed to connect upstream", { status: 502 });
      }
      upstream.accept();

      // Bridge messages both ways
      server.addEventListener("message", ev => { try { upstream.send(ev.data); } catch {} });
      upstream.addEventListener("message", ev => { try { server.send(ev.data); } catch {} });

      // Mirror close/error both ways
      server.addEventListener("close", ev => { try { upstream.close(ev.code, ev.reason || "client closed"); } catch {} });
      upstream.addEventListener("close", ev => { try { server.close(ev.code, ev.reason || "upstream closed"); } catch {} });
      server.addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });
      upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

      // Keep-alive ping to prevent idle disconnects
      const ping = setInterval(() => {
        try { server.send(JSON.stringify({ type: "ping", t: Date.now() })); } catch { clearInterval(ping); }
      }, 30000);

      ctx.waitUntil(new Promise<void>(resolve => {
        const done = () => { clearInterval(ping); resolve(); };
        server.addEventListener("close", done);
        upstream.addEventListener("close", done);
      }));

      // Complete the handshake (echo subprotocol)
      const respHeaders = new Headers();
      if (proto) respHeaders.set("Sec-WebSocket-Protocol", proto);
      return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
    }

    // Fallback for other paths
    return new Response("OK", { status: 200 });
  }
};
