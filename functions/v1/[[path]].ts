type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // default https://api.openai.com
};

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "*",
    "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "cache-control": "no-store"
  };
}

function json(body: unknown, status = 200, extra: Record<string,string> = {}) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...corsHeaders(), ...extra }
  });
}

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  // Policy: block moderations on this relay
  if (url.pathname.startsWith("/v1/moderations")) {
    return json({ error: { message: "blocked" } }, 404);
  }

  // Hint users that /v1/realtime must use the Worker (WS upgrade)
  if (url.pathname.startsWith("/v1/realtime")) {
    const hint = { error: { message: "Use the Realtime Worker for WebSocket upgrades (wss). This Pages relay is HTTP-only." } };
    return json(hint, 426); // 426 Expected WebSocket Upgrade
  }

  // Only relay /v1/*
  if (!url.pathname.startsWith("/v1/")) {
    return new Response("Not Found", { status: 404 });
  }

  // Upstream URL
  const base = (env.BASE || "https://api.openai.com").replace(/\/$/, "");
  const upstreamUrl = base + url.pathname + url.search;

  // Forward headers; inject server-side Authorization if client omitted
  const out = new Headers(request.headers);
  if (!out.get("authorization") && env.OPENAI_KEY) {
    out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  }
  if (env.OPENAI_ORG_ID && !out.has("openai-organization")) out.set("openai-organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT && !out.has("openai-project")) out.set("openai-project", env.OPENAI_PROJECT);
  if (env.OPENAI_BETA    && !out.has("openai-beta"))    out.set("openai-beta", env.OPENAI_BETA);

  // Strip hop-by-hop
  for (const h of ["host","content-length","connection","transfer-encoding","keep-alive","upgrade"]) out.delete(h);

  const method = request.method.toUpperCase();
  const ct = request.headers.get("content-type") || "";
  const isMultipart = ct.includes("multipart/form-data");

  // If multipart (files/audio), reconstruct to preserve boundaries
  let body: BodyInit | null = null;
  if (["GET","HEAD"].includes(method)) {
    body = null;
  } else if (isMultipart) {
    const form = await request.formData();
    const copy = new FormData();
    for (const [k, v] of form.entries()) copy.append(k, v as any);
    body = copy;
    out.delete("content-type"); // boundary will be set by fetch from FormData
  } else {
    body = request.body; // stream JSON/bytes through
  }

  const upstream = await fetch(upstreamUrl, { method, headers: out, body });
  // Mirror upstream status/headers; keep CORS/cache headers
  const headers = new Headers(upstream.headers);
  for (const [k,v] of Object.entries(corsHeaders())) headers.set(k, v);
  return new Response(upstream.body, { status: upstream.status, headers });
};
