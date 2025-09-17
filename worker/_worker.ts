// Cloudflare Worker: Realtime WS bridge using fetch+Upgrade client socket (recommended for custom headers).
export interface Env {
  OPENAI_KEY: string;           // secret
  OPENAI_ORG_ID?: string;       // plaintext
  OPENAI_PROJECT?: string;      // plaintext
  OPENAI_BETA?: string;         // plaintext; default realtime=v1
}
export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // health
    if (url.pathname === "/v1/health-rt") {
      return new Response(JSON.stringify({ ok: true, service: "realtime" }), {
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
      });
    }

    if (url.pathname !== "/v1/realtime") return new Response("Not Found (realtime worker)", { status: 404 });
    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") return new Response("Expected WebSocket upgrade", { status: 426 });

    // server side of the pair for the client <-> worker hop
    // @ts-ignore
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair);
    // @ts-ignore
    server.accept();

    // negotiate subprotocol with client; default to oai-realtime
    const clientProto = (req.headers.get("Sec-WebSocket-Protocol") || "").trim();
    const protocol = clientProto || "oai-realtime";

    // build upstream URL and headers
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;
    const headers: Record<string,string> = {
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA?.trim() || "realtime=v1"),
      "Upgrade": "websocket",
      "Sec-WebSocket-Protocol": protocol
    };
    if (env.OPENAI_ORG_ID)  headers["OpenAI-Organization"] = env.OPENAI_ORG_ID;
    if (env.OPENAI_PROJECT) headers["OpenAI-Project"]      = env.OPENAI_PROJECT;

    // open client websocket to OpenAI via fetch+Upgrade
    const resp = await fetch(upstreamUrl, { method: "GET", headers });
    const upstream = (resp as any).webSocket as WebSocket | undefined;
    if (!upstream) {
      const txt = await resp.text();
      return new Response("Upstream WS failed: " + resp.status + " " + txt, { status: 502 });
    }
    upstream.accept();

    // bridge frames both ways
    server.addEventListener("message", (e: MessageEvent) => { try { upstream.send(e.data); } catch {} });
    upstream.addEventListener("message", (e: MessageEvent) => { try { server.send(e.data); } catch {} });

    server.addEventListener("close", (e: any) => { try { upstream.close(e.code, e.reason || "client closed"); } catch {} });
    upstream.addEventListener("close", (e: any) => { try { server.close(e.code, e.reason || "upstream closed"); } catch {} });

    server.addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });
    upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });

    // return 101 and echo chosen subprotocol to client (WS spec)
    const out = new Headers(); out.set("Sec-WebSocket-Protocol", protocol);
    return new Response(null, { status: 101, webSocket: client, headers: out });
  }
};
