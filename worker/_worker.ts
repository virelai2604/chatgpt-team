export interface Env {
  OPENAI_KEY: string;
  OPENAI_BETA?: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/v1/realtime"))
      return new Response("Not Found (realtime worker)", { status: 404 });
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket")
      return new Response("Expected WebSocket upgrade", { status: 426 });

    // @ts-ignore - WebSocketPair is a Cloudflare extension
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    // Required headers for OpenAI Realtime
    const hdrs = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": env.OPENAI_BETA || "realtime=v1",
    });
    if (env.OPENAI_ORG_ID) hdrs.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) hdrs.set("OpenAI-Project", env.OPENAI_PROJECT);

    const upstreamResp = await fetch(upstreamUrl, { headers: hdrs, method: "GET" });
    const upstream = (upstreamResp as any).webSocket;
    if (!upstream) {
      server.close(1011, "Upstream refused websocket");
      return new Response("Upstream refused websocket", { status: upstreamResp.status || 502 });
    }
    upstream.accept();

    server.addEventListener("message", (e: MessageEvent) => upstream.send(e.data));
    upstream.addEventListener("message", (e: MessageEvent) => server.send(e.data));
    server.addEventListener("close", () => upstream.close());
    upstream.addEventListener("close", () => server.close());
    server.addEventListener("error", () => upstream.close(1011));
    upstream.addEventListener("error", () => server.close(1011));

    // Echo client's protocol back so wscat/websockets are happy
    const respHeaders = new Headers();
    const proto = req.headers.get("Sec-WebSocket-Protocol");
    if (proto) respHeaders.set("Sec-WebSocket-Protocol", proto);

    return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
  }
};