type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // optional: override upstream (defaults to https://api.openai.com)
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  // Hard block Moderations by policy
  if (url.pathname.startsWith("/v1/moderations")) {
    return json({ error: { message: "blocked" } }, 404, corsHeaders());
  }

  // Only handle /v1/*
  if (!url.pathname.startsWith("/v1/")) {
    return new Response("Not found", { status: 404 });
  }

  // Compute upstream URL
  const upstreamBase = (env.BASE && env.BASE.trim()) || "https://api.openai.com";
  const upstreamUrl = upstreamBase + url.pathname + url.search;

  // Build outbound headers
  const out = new Headers(request.headers);

  // Always use the server-side key; ignore any client Authorization
  out.set("Authorization", `Bearer ${env.OPENAI_KEY}`);

  if (env.OPENAI_ORG_ID)  out.set("OpenAI-Organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT) out.set("OpenAI-Project",      env.OPENAI_PROJECT);
  if (env.OPENAI_BETA)    out.set("OpenAI-Beta",         env.OPENAI_BETA);

  // Strip hop-by-hop headers
  out.delete("host");
  out.delete("content-length");
  out.delete("connection");
  out.delete("transfer-encoding");
  out.delete("keep-alive");
  out.delete("upgrade");

  const method = request.method.toUpperCase();
  const ct = request.headers.get("content-type") || "";
  const isMultipart = ct.includes("multipart/form-data");

  let init: RequestInit;
  if (isMultipart) {
    const form = await request.formData();
    const f = new FormData();
    for (const [k, v] of form.entries()) f.append(k, v as any);
    init = { method, headers: out, body: f };
  } else {
    init = { method, headers: out, body: ["GET","HEAD"].includes(method) ? undefined : request.body };
  }

  const resp = await fetch(upstreamUrl, init);

  // Prepare response headers (no hop-by-hop) + CORS
  const rh = new Headers(resp.headers);
  rh.delete("content-length");
  rh.delete("connection");
  rh.delete("transfer-encoding");
  rh.delete("keep-alive");
  rh.delete("upgrade");
  for (const [k,v] of Object.entries(corsHeaders())) rh.set(k,v);

  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: rh });
};

function corsHeaders(): Record<string,string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Requested-With, Accept"
  };
}

function json(data: unknown, status = 200, headers: Record<string,string> = {}) {
  const h = new Headers({ "content-type": "application/json; charset=utf-8", ...headers });
  return new Response(JSON.stringify(data), { status, headers: h });
}