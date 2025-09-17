type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // optional override, default https://api.openai.com
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

  // Block Moderations by policy (intentional)
  if (url.pathname.startsWith("/v1/moderations")) {
    return json({ error: { message: "blocked" } }, 404, corsHeaders());
  }

  // Build upstream URL
  const base = (env.BASE || "https://api.openai.com").replace(/\/$/, "");
  const upstreamUrl = base + url.pathname + url.search;

  // Prepare outbound headers (copy only what's needed)
  const out = new Headers();
  const fwd = request.headers;
  for (const [k, v] of fwd.entries()) {
    const lower = k.toLowerCase();
    if (lower === "content-type" || lower === "accept" || lower === "accept-language" || lower === "range") {
      out.set(k, v);
    }
  }

  // Server-side auth and optional org/project/beta
  out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  if (env.OPENAI_ORG_ID) out.set("OpenAI-Organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT) out.set("OpenAI-Project", env.OPENAI_PROJECT);
  if (env.OPENAI_BETA)    out.set("OpenAI-Beta", env.OPENAI_BETA!);

  const canHaveBody = !(request.method === "GET" || request.method === "HEAD");

  // Stream through; do not re-construct multipart
  let resp: Response;
  try {
    resp = await fetch(upstreamUrl, {
      method: request.method,
      headers: out,
      body: canHaveBody ? request.body : undefined
    });
  } catch (err: any) {
    return json({ ok: false, error: String(err) }, 502, corsHeaders());
  }

  // CORS + no-store passthrough
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set("Access-Control-Expose-Headers", "OpenAI-*, X-Request-Id");
  rh.set("Cache-Control", "no-store");

  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: rh });
};

function corsHeaders(): Record<string,string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Requested-With, Accept"
  };
}

function json(data: unknown, status = 200, extra: Record<string,string> = {}) {
  const h = new Headers({ "content-type": "application/json; charset=utf-8", ...extra });
  return new Response(JSON.stringify(data, null, 2), { status, headers: h });
}