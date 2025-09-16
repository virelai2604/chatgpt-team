export interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // if not set, we default to 'realtime=v1'
}

/**
 * Routes:
 *  - GET /v1/health-rt     -> JSON, env sanity
 *  - GET /v1/realtime?...  -> WebSocket upgrade; proxied to OpenAI Realtime
 */
export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Lightweight health check
    if (url.pathname === "/v1/health-rt") {
      return new Response(
        JSON.stringify({
          ok: true,
          upstream: "wss://api.openai.com/v1/realtime",
          modelDefault: "gpt-4o-realtime-preview-2024-12-17",
          env: {
            OPENAI_KEY: !!env.OPENAI_KEY,
            OPENAI_ORG_ID: !!env.OPENAI_ORG_ID,
            OPENAI_PROJECT: !!env.OPENAI_PROJECT,
            OPENAI_BETA: env.OPENAI_BETA ?? null,
          },
        }),
        {
          headers: {
            "content-type": "application/json; charset=utf-8",
            "access-control-allow-origin": "*",
          },
        }
      );
    }

    // Only handle realtime upgrades here
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime worker)", { status: 404 });
    }

    // Must be a WS upgrade
    const upgrade = (req.headers.get("Upgrade") || "").toLowerCase();
    if (upgrade !== "websocket") {
      return new Response("Expected WebSocket upgrade", { status: 426 });
    }

    // Create local pair and accept the server side
    // @ts-ignore WebSocketPair type is provided by CF runtime
    const pair = new WebSocketPair();
    // @ts-ignore
    const [client, server] = Object.values(pair) as [WebSocket, WebSocket];
    // @ts-ignore
    server.accept();

    // Build upstream URL and headers for OpenAI Realtime
    const model =
      url.searchParams.get("model") || "gpt-4o-realtime-preview-2024-12-17";

    const upstreamUrl = https://api.openai.com/v1/realtime?model=;

    const headers: Record<string, string> = {
      Upgrade: "websocket",
      Authorization: Bearer ,
      "OpenAI-Beta": env.OPENAI_BETA || "realtime=v1",
    };
    if (env.OPENAI_ORG_ID) headers["OpenAI-Organization"] = env.OPENAI_ORG_ID;
    if (env.OPENAI_PROJECT) headers["OpenAI-Project"] = env.OPENAI_PROJECT;

    // Connect to upstream WS (Workers supports upgrading via fetch with headers)
    const upstreamResp = await fetch(upstreamUrl, { headers });
    // @ts-ignore
    const upstream = upstreamResp.webSocket as WebSocket | undefined;
    if (!upstream) {
      try {
        server.send(
          JSON.stringify({
            type: "error",
            error: {
              message: Upstream refused WebSocket (status ),
            },
          })
        );
      } catch {}
      server.close(1011, "Upstream refused WebSocket");
      return new Response("Upstream refused WebSocket", {
        status: upstreamResp.status,
      });
    }
    // @ts-ignore
    upstream.accept();

    // Bi-directional piping
    const pipe = (from: WebSocket, to: WebSocket) => {
      from.addEventListener("message", (evt: any) => {
        try {
          to.send(evt.data);
        } catch {
          try { to.close(1011, "send error"); } catch {}
        }
      });
      from.addEventListener("close", (evt: any) => {
        try { to.close(evt.code, evt.reason); } catch {}
      });
      from.addEventListener("error", () => {
        try { to.close(1011, "error"); } catch {}
      });
    };

    pipe(server, upstream);
    pipe(upstream, server);

    // Return the client end to the browser
    return new Response(null, { status: 101, webSocket: client });
  },
};
