type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // default api.openai.com
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers":
          "Authorization, Content-Type, OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Requested-With, Accept",
      },
    });
  }

  // Block moderation per policy
  if (url.pathname.startsWith("/v1/moderations")) {
    return new Response(JSON.stringify({ error: { message: "blocked" } }), {
      status: 404,
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
        "access-control-allow-origin": "*",
      },
    });
  }

  // Only handle /v1/*
  if (!url.pathname.startsWith("/v1/")) {
    return new Response("Not found", { status: 404 });
  }

  // Upstream target
  const base = env.BASE || "https://api.openai.com";
  const upstream = new URL(base + url.pathname + url.search);

  // Forward headers and inject server-side auth
  const out = new Headers(request.headers);
  if (!out.has("authorization") && env.OPENAI_KEY) {
    out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  }
  if (env.OPENAI_ORG_ID && !out.has("openai-organization")) {
    out.set("openai-organization", env.OPENAI_ORG_ID);
  }
  if (env.OPENAI_PROJECT && !out.has("openai-project")) {
    out.set("openai-project", env.OPENAI_PROJECT);
  }
  if (env.OPENAI_BETA && !out.has("openai-beta")) {
    out.set("openai-beta", env.OPENAI_BETA);
  }
  // Strip hop-by-hop headers; let the platform compute length/host
  out.delete("host"); out.delete("content-length"); out.delete("connection");
  out.delete("transfer-encoding"); out.delete("keep-alive"); out.delete("upgrade");

  const method = request.method.toUpperCase();
  const ct = request.headers.get("content-type") || "";
  const isMultipart = ct.includes("multipart/form-data");

  let init: RequestInit;
  if (isMultipart) {
    // Rebuild multipart to preserve boundaries
    const form = await request.formData();
    const f = new FormData();
    for (const [k, v] of form.entries()) f.append(k, v as any);
    const mh = new Headers({ authorization: out.get("authorization")! });
    if (out.get("openai-organization")) mh.set("openai-organization", out.get("openai-organization")!);
    if (out.get("openai-project")) mh.set("openai-project", out.get("openai-project")!);
    if (out.get("openai-beta")) mh.set("openai-beta", out.get("openai-beta")!);
    init = { method, headers: mh, body: f, redirect: "manual" };
  } else {
    init = {
      method,
      headers: out,
      body: (method === "GET" || method === "HEAD") ? undefined : request.body,
      redirect: "manual",
    };
  }

  const resp = await fetch(upstream.toString(), init);
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set("Access-Control-Expose-Headers",
    "OpenAI-Processing-Ms, OpenAI-Organization, OpenAI-Version, OpenAI-Model, X-Request-Id");
  rh.set("Cache-Control", "no-store");

  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: rh });
};