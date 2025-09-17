// Minimal WS bridge: requires Upgrade: websocket; negotiates/echoes "oai-realtime"; forwards Authorization and OpenAI-Beta upstream.
export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // keep 'realtime=v1' as plaintext default at Worker level
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/v1/realtime")) return new Response("Not Found (realtime worker)", { status: 404 });

    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Client <-> Worker sockets
    // @ts-ignore
    const pair = new WebSocketPair(); 
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    // Subprotocol: default to 'oai-realtime' if client didn't send one
    const clientProto = (req.headers.get("Sec-WebSocket-Protocol") || "").trim();
    const subproto = clientProto || "oai-realtime";

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstream = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    const headers: Record<string,string> = {
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA || "realtime=v1"),
      "Connection": "upgrade",
      "Upgrade": "websocket",
    };
    if (env.OPENAI_ORG_ID) headers["OpenAI-Organization"] = env.OPENAI_ORG_ID;
    if (env.OPENAI_PROJECT) headers["OpenAI-Project"] = env.OPENAI_PROJECT;

    const upstreamResp = await fetch(upstream, {
      method: "GET",
      headers,
      // Pass through the negotiated subprotocol to upstream:
      webSocket: { protocol: subproto } as any
    });

    if (upstreamResp.status !== 101 || !upstreamResp.webSocket) {
      const txt = await upstreamResp.text();
      return new Response("Upstream WS failed: " + upstreamResp.status + " " + txt, { status: 502 });
    }

    const upstreamWS = upstreamResp.webSocket as WebSocket;

    // Pump bytes both ways
    server.addEventListener("message", (e) => upstreamWS.send(e.data));
    upstreamWS.addEventListener("message", (e) => server.send(e.data));
    server.addEventListener("close", () => upstreamWS.close(1000, "client closed"));
    upstreamWS.addEventListener("close", () => server.close(1000, "upstream closed"));
    server.addEventListener("error", () => upstreamWS.close(1011, "client error"));
    upstreamWS.addEventListener("error", () => server.close(1011, "upstream error"));

    // Return 101 with the echoed subprotocol
    return new Response(null, { status: 101, webSocket: client, headers: { "Sec-WebSocket-Protocol": subproto } });
  }
};