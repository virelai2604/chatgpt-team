export default {
  async fetch(req: Request, env: any) {
    const url = new URL(req.url);

    // Only handle /v1/realtime here
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime worker)", { status: 404 });
    }

    // Expect a WebSocket upgrade
    const up = (req.headers.get("Upgrade") || "").toLowerCase();
    if (up !== "websocket") return new Response("Expected WebSocket", { status: 426 });

    // If UPSTREAM_REALTIME != "1", return a local 101 (loopback) so smoke tests pass
    const proxyUpstream = env.UPSTREAM_REALTIME === "1";

    // Always accept a server-side socket to return to the client
    // @ts-ignore - Cloudflare runtime
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    if (!proxyUpstream) {
      // Minimal hello for CI smoke; client just needs 101
      // @ts-ignore
      setTimeout(() => { try { server.send(JSON.stringify({ ok: true, hello: "realtime" })); } catch {} }, 10);
      // @ts-ignore
      return new Response(null, { status: 101, webSocket: client });
    }

    // Build upstream URL to OpenAI Realtime
    const model = url.searchParams.get("model") || "gpt-4o-realtime-preview-2024-12-17";
    const upstream = new URL(`wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`);

    // Clone incoming headers and inject server-side auth if needed
    const out = new Headers(req.headers);
    if (!out.has("authorization")) {
      const key = env.OPENAI_KEY;
      if (!key) return new Response("Server OPENAI_KEY not set", { status: 500 });
      out.set("authorization", `Bearer ${key}`);
    }
    if (env.OPENAI_ORG_ID && !out.has("openai-organization")) out.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT  && !out.has("openai-project"))     out.set("OpenAI-Project",      env.OPENAI_PROJECT);
    if (env.OPENAI_BETA     && !out.has("openai-beta"))        out.set("OpenAI-Beta",         env.OPENAI_BETA);

    // Ensure upgrade headers (Workers passes these through)
    out.set("Connection", "Upgrade");
    out.set("Upgrade", "websocket");

    // Most clients use GET for WS
    const method = req.method || "GET";

    // Proxy the upgrade via fetch; Cloudflare returns a Response with a webSocket on 101
    const resp = await fetch(new Request(upstream.toString(), { method, headers: out }));

    if (resp.status !== 101) {
      // Upstream didn’t switch protocols; just relay the response
      return resp;
    }

    // @ts-ignore - Cloudflare Response has a webSocket property for WS upgrades
    const { webSocket: upstreamSocket } = resp as any;
    if (!upstreamSocket) return new Response("Upstream 101 but no webSocket", { status: 502 });

    // Pipe messages between client<->upstream
    // @ts-ignore
    server.addEventListener("message", (e: MessageEvent) => { try { upstreamSocket.send(e.data); } catch {} });
    // @ts-ignore
    upstreamSocket.addEventListener("message", (e: MessageEvent) => { try { server.send(e.data); } catch {} });

    // Close propagation
    // @ts-ignore
    server.addEventListener("close", () => { try { upstreamSocket.close(1000, "client closed"); } catch {} });
    // @ts-ignore
    upstreamSocket.addEventListener("close", () => { try { server.close(1000, "upstream closed"); } catch {} });

    // Error propagation (best-effort)
    // @ts-ignore
    server.addEventListener("error", () => { try { upstreamSocket.close(1011, "client error"); } catch {} });
    // @ts-ignore
    upstreamSocket.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // Hand back the accepted socket to the client
    // @ts-ignore
    return new Response(null, { status: 101, webSocket: client });
  }
}
