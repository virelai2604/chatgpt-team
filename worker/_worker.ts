export interface Env {
  OPENAI_KEY: string;                // set as a Secret in CF (Dashboard or `wrangler secret put`)
  OPENAI_ORG_ID?: string;            // optional, plaintext in CF if you need it
  OPENAI_PROJECT?: string;           // optional, plaintext in CF if you need it
  OPENAI_BETA?: string;              // "realtime=v1" (set in vars)
  BASE?: string;                     // e.g. "api.openai.com" (default)
}

/**
 * Minimal WebSocket pass-through:
 * - Only handles /v1/realtime
 * - Forces Authorization to the Worker secret (never trusts client header)
 * - Adds OpenAI-Beta + optional org/project headers
 * - Lets Cloudflare handle the 101 and stream thereafter
 */
export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/v1/realtime")) {
      return new Response("Not Found (realtime worker)", { status: 404 });
    }

    const upgrade = (req.headers.get("Upgrade") || "").toLowerCase();
    if (upgrade !== "websocket") {
      return new Response("Expected WebSocket upgrade", {
        status: 426,
        headers: {
          "Connection": "Upgrade",
          "Upgrade": "websocket",
        },
      });
    }

    // Default model if caller does not specify
    const model = url.searchParams.get("model") || "gpt-4o-realtime-preview-2024-12-17";
    const host = env.BASE || "api.openai.com";
    const upstream = `https://${host}/v1/realtime?model=${encodeURIComponent(model)}`;

    // Build headers for upstream
    const h = new Headers();
    h.set("Authorization", `Bearer ${env.OPENAI_KEY}`);
    h.set("OpenAI-Beta", env.OPENAI_BETA || "realtime=v1");
    if (env.OPENAI_ORG_ID) h.set("OpenAI-Organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT) h.set("OpenAI-Project", env.OPENAI_PROJECT);

    // Proxy the WS handshake to OpenAI. Returning the fetch Response is enough;
    // Workers runtime will complete the 101 switch and stream both ways.
    return fetch(upstream, new Request(req, { headers: h, method: "GET" }));
  },
};