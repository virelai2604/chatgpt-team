export default {
  async fetch(req: Request, env: any) {
    const url = new URL(req.url)
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime worker)", { status: 404 })
    }

    // Expect a WS upgrade
    const up = (req.headers.get("Upgrade") || "").toLowerCase()
    if (up !== "websocket") return new Response("Expected WebSocket", { status: 426 })

    // Toggle: loopback vs upstream pass-through
    const useUpstream = (env.UPSTREAM_REALTIME === "1")

    // Always accept a local server socket for the client
    // @ts-ignore
    const pair = new WebSocketPair()
    // @ts-ignore
    const [client, server] = Object.values(pair)
    // @ts-ignore
    server.accept()

    if (!useUpstream) {
      // LOOPBACK MODE (CI/Smoke): send hello and close so curl exits
      // @ts-ignore
      server.send(JSON.stringify({ ok: true, mode: "loopback", ts: new Date().toISOString() }))
      // @ts-ignore
      server.close(1000, "ok")
      // @ts-ignore
      return new Response(null, { status: 101, webSocket: client })
    }

    // UPSTREAM MODE (PROD): connect to OpenAI Realtime and pipe bytes both ways
    const model = url.searchParams.get("model") || "gpt-4o-realtime-preview-2024-12-17"
    const upstreamUrl = new URL(req.url)
    upstreamUrl.protocol = "https:"
    upstreamUrl.hostname = "api.openai.com"
    upstreamUrl.port = ""
    upstreamUrl.pathname = "/v1/realtime"
    upstreamUrl.search = "?model=" + encodeURIComponent(model)

    // Build headers
    const h = new Headers(req.headers)
    // Ensure upgrade request
    h.set("Connection", "Upgrade")
    h.set("Upgrade", "websocket")

    // Inject server-side auth if client didn’t pass one
    if (!h.has("Authorization")) {
      const key = env.OPENAI_KEY
      if (!key) {
        // @ts-ignore
        server.send(JSON.stringify({ ok:false, error:"OPENAI_KEY missing in Worker env" }))
        // @ts-ignore
        server.close(1011, "server config")
        // @ts-ignore
        return new Response(null, { status: 101, webSocket: client })
      }
      h.set("Authorization", `Bearer ${key}`)
    }
    if (env.OPENAI_ORG_ID)  h.set("OpenAI-Organization", env.OPENAI_ORG_ID)
    if (env.OPENAI_PROJECT) h.set("OpenAI-Project",      env.OPENAI_PROJECT)
    if (env.OPENAI_BETA)    h.set("OpenAI-Beta",         env.OPENAI_BETA)

    // Perform the upstream upgrade
    const upstreamResp = await fetch(upstreamUrl.toString(), { method: "GET", headers: h })
    // @ts-ignore
    const upstreamSocket = (upstreamResp as any).webSocket
    if (upstreamResp.status !== 101 || !upstreamSocket) {
      // @ts-ignore
      server.send(JSON.stringify({ ok:false, status: upstreamResp.status, error:"Upstream refused upgrade" }))
      // @ts-ignore
      server.close(1011, "upstream refused")
      // @ts-ignore
      return new Response(null, { status: 101, webSocket: client })
    }
    // @ts-ignore
    upstreamSocket.accept()

    // Bi-directional piping
    // @ts-ignore
    server.addEventListener("message", (e: MessageEvent) => {
      try { upstreamSocket.send(e.data) } catch {}
    })
    // @ts-ignore
    upstreamSocket.addEventListener("message", (e: MessageEvent) => {
      try { server.send(e.data) } catch {}
    })

    // Close propagation
    // @ts-ignore
    server.addEventListener("close", () => { try { upstreamSocket.close(1000, "client closed") } catch {} })
    // @ts-ignore
    upstreamSocket.addEventListener("close", () => { try { server.close(1000, "upstream closed") } catch {} })

    // Error propagation (best-effort)
    // @ts-ignore
    server.addEventListener("error", () => { try { upstreamSocket.close(1011, "client error") } catch {} })
    // @ts-ignore
    upstreamSocket.addEventListener("error", () => { try { server.close(1011, "upstream error") } catch {} })

    // @ts-ignore
    return new Response(null, { status: 101, webSocket: client })
  }
}