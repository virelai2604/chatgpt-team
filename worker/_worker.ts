export interface Env {
  OPENAI_KEY: string;                 // secret
  OPENAI_BETA?: string;               // plaintext e.g., "realtime=v1"
  OPENAI_ORG_ID?: string;             // plaintext
  OPENAI_PROJECT?: string;            // plaintext
}
export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname !== "/v1/realtime") return new Response("Not Found (realtime worker)", { status: 404 });

    if ((req.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Create pair; accept server side
    // @ts-ignore
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair) as [WebSocket, WebSocket];
    // @ts-ignore
    server.accept();

    // Upstream OpenAI Realtime
    const model = url.searchParams.get("model") ?? "gpt-4o-realtime-preview-2024-12-17";
    const upstreamUrl = `wss://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`;

    // Subprotocol: default to 'oai-realtime' if client didn't send one
    const clientProto = req.headers.get("Sec-WebSocket-Protocol") || "oai-realtime";

    // Required headers for OpenAI Realtime
    const headers = new Headers({
      "Authorization": `Bearer ${env.OPENAI_KEY}`,
      "OpenAI-Beta": (env.OPENAI_BETA?.trim() || "realtime=v1"),
    });
    if (env.OPENAI_ORG_ID)  headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) headers.set("OpenAI-Project",       env.OPENAI_PROJECT);

    // Connect upstream as WS client; include the negotiated protocol
    // @ts-ignore - Workers supports new WebSocket(url, protocols, { headers })
    const upstream = new WebSocket(upstreamUrl, clientProto ? [clientProto] : undefined, { headers } as any);

    // Bridge frames both directions
    upstream.addEventListener("message", (ev: MessageEvent) => { try { server.send(ev.data); } catch {} });
    server .addEventListener("message", (ev: MessageEvent) => { try { upstream.send(ev.data); } catch {} });

    upstream.addEventListener("close", (ev: any) => { try { server.close(ev.code, ev.reason || "upstream closed"); } catch {} });
    server .addEventListener("close", (ev: any) => { try { upstream.close(ev.code, ev.reason || "client closed"); } catch {} });

    upstream.addEventListener("error", () => { try { server.close(1011, "upstream error"); } catch {} });
    server .addEventListener("error", () => { try { upstream.close(1011, "client error"); } catch {} });

    // Echo chosen subprotocol back to client per WS spec
    const respHeaders = new Headers();
    if (clientProto) respHeaders.set("Sec-WebSocket-Protocol", clientProto);

    return new Response(null, { status: 101, webSocket: client, headers: respHeaders });
  }
};
