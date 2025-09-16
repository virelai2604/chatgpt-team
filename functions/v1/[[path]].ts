type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // default https://api.openai.com
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  // Only relay /v1/*
  if (!url.pathname.startsWith("/v1/")) {
    return json({ ok: false, error: "Not Found" }, 404, corsHeaders());
  }

  // Relay policy: hard‑block Moderations at the edge
  if (url.pathname.startsWith("/v1/moderations")) {
    return json({ error: "endpoint disabled at relay" }, 404, corsHeaders());
  }

  // Build upstream URL
  const base = (env.BASE || "https://api.openai.com").replace(/\/$/, "");
  const upstreamUrl = base + url.pathname + url.search;

  // Prepare outbound headers
  const out = new Headers();
  for (const [k, v] of request.headers.entries()) {
    const lower = k.toLowerCase();
    if (lower === "content-type" || lower === "accept" || lower === "accept-language" || lower === "range") {
      out.set(k, v);
    }
  }

  // Always set auth from env — never trust client
  out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  if (env.OPENAI_ORG_ID) out.set("OpenAI-Organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT) out.set("OpenAI-Project", env.OPENAI_PROJECT);
  if (env.OPENAI_BETA)    out.set("OpenAI-Beta", env.OPENAI_BETA!);

  const canHaveBody = !(request.method === "GET" || request.method === "HEAD");
  const init: RequestInit = { method: request.method, headers: out, body: canHaveBody ? request.body : undefined };

  let resp: Response;
  try { resp = await fetch(upstreamUrl, init); }
  catch (err: any) { return json({ ok: false, error: String(err) }, 502, corsHeaders()); }

  // Mirror upstream response, add permissive CORS
  const headers = new Headers(resp.headers);
  const cors = corsHeaders();
  for (const [k, v] of Object.entries(cors)) headers.set(k, v);

  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers });
};

function corsHeaders(): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers":
      "Authorization, Content-Type, OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Requested-With, Accept",
    "Access-Control-Expose-Headers":
      "Content-Type, X-Request-Id, OpenAI-Organization, OpenAI-Project",
  };
}

function json(data: unknown, status = 200, extra: Record<string, string> = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...extra },
  });
}