export default {
  async fetch(req: Request, env: any) {
    const url = new URL(req.url);

    // Only handle /v1/realtime here
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime worker)", { status: 404 });
    }

    // Expect a WebSocket upgrade
    const upgrade = (req.headers.get("Upgrade") || "").toLowerCase();
    if (upgrade !== "websocket") return new Response("Expected WebSocket", { status: 426 });

    // Decide whether to proxy upstream or loopback
    const upstreamOn = String(env.UPSTREAM_REALTIME ?? "1").trim() !== "0";

    // Accept server-side socket to return to client
    // @ts-ignore
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    // Loopback mode for smoke tests
    if (!upstreamOn) {
      // @ts-ignore
      setTimeout(() => { try { server.send(JSON.stringify({ ok: true, mode: "loopback", ts: new Date().toISOString() })); } catch {} }, 0);
      // @ts-ignore
      return new Response(null, { status: 101, webSocket: client });
    }

    // Proxy to OpenAI Realtime (HTTPS + Upgrade)
    const model = url.searchParams.get("model") || "gpt-4o-realtime-preview-2024-12-17";

    if (!env.OPENAI_KEY) {
      // @ts-ignore
      server.close(1011, "OPENAI_KEY missing");
      return new Response("OPENAI_KEY missing", { status: 500 });
    }

    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const headers = new Headers();
    // Always inject server-side auth and required headers
    headers.set("Authorization", `Bearer ${env.OPENAI_KEY}`);
    if (env.OPENAI_PROJECT)      headers.set("OpenAI-Project",      env.OPENAI_PROJECT);
    if (env.OPENAI_ORG_ID)       headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    headers.set("OpenAI-Beta", "realtime=v1");
    headers.set("Connection", "Upgrade");
    headers.set("Upgrade", "websocket");
    headers.set("Sec-WebSocket-Version", "13");

    let upstreamResp: Response;
    try {
      upstreamResp = await fetch(upstreamUrl, { method: "GET", headers });
    } catch (err: any) {
      // @ts-ignore
      server.close(1011, "Fetch to upstream failed");
      return new Response("Upstream fetch failed", { status: 502 });
    }

    // If upstream didn't switch protocols, bubble status/body
    if (upstreamResp.status !== 101) {
      const body = await upstreamResp.text().catch(() => "");
      // @ts-ignore
      server.close(1011, `Upstream ${upstreamResp.status}`);
      return new Response(body || `Upstream error ${upstreamResp.status}`, { status: upstreamResp.status });
    }

    // @ts-ignore - Cloudflare Response contains a webSocket on 101
    const upstreamSocket = (upstreamResp as any).webSocket;
    if (!upstreamSocket) {
      // @ts-ignore
      server.close(1011, "No upstream socket");
      return new Response("Upstream 101 but no webSocket", { status: 502 });
    }

    // Pipe messages between client <-> upstream
    // @ts-ignore
    server.addEventListener("message", (e: MessageEvent) => { try { upstreamSocket.send(e.data); } catch {} });
    upstreamSocket.addEventListener("message", (e: MessageEvent) => { try { server.send(e.data); } catch {} });

    // Close propagation
    // @ts-ignore
    server.addEventListener("close",   () => { try { upstreamSocket.close(1000, "client closed"); } catch {} });
    upstreamSocket.addEventListener("close", () => { try { server.close(1000, "upstream closed"); } catch {} });

    // Error propagation
    // @ts-ignore
    server.addEventListener("error",   () => { try { upstreamSocket.close(1011, "client error"); } catch {} });
    upstreamSocket.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // Hand back the accepted socket to the client
    // @ts-ignore
    return new Response(null, { status: 101, webSocket: client });
  }
}