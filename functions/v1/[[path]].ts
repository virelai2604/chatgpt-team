// Cloudflare Pages Functions – catch-all proxy to OpenAI /v1/*
type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // optional: override upstream base
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers":
          "Authorization, Content-Type, OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Requested-With, Accept",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS",
        "Access-Control-Max-Age": "86400",
      },
    });
  }

  // Only proxy /v1/*
  if (!url.pathname.startsWith("/v1/")) {
    return new Response("Not found", { status: 404 });
  }
  // Hide Moderations
  if (url.pathname.startsWith("/v1/moderations")) {
    return new Response("Moderations endpoint disabled", { status: 403 });
  }

  // Build upstream URL
  const base = env.BASE || "https://api.openai.com";
  const upstream = new URL(url.pathname + url.search, base).toString();

  // Build headers from scratch (avoid leaking client-only headers)
  const out = new Headers();
  out.set("Authorization", Bearer );
  const ct = request.headers.get("content-type");
  if (ct) out.set("content-type", ct);

  if (env.OPENAI_ORG_ID) out.set("OpenAI-Organization", env.OPENAI_ORG_ID);
  const clientProject = request.headers.get("OpenAI-Project");
  if (clientProject) out.set("OpenAI-Project", clientProject);
  if (env.OPENAI_PROJECT && !clientProject) out.set("OpenAI-Project", env.OPENAI_PROJECT);
  if (env.OPENAI_BETA) out.set("OpenAI-Beta", env.OPENAI_BETA);

  // Auto-enable assistants v2 when path matches
  const p = url.pathname;
  if (p.startsWith("/v1/assistants") || p.startsWith("/v1/threads") || p.includes("/runs")) {
    if (!out.has("OpenAI-Beta")) out.set("OpenAI-Beta", "assistants=v2");
  }

  const init: RequestInit = {
    method: request.method,
    headers: out,
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = request.body;
  }

  const resp = await fetch(upstream, init);

  // CORS + expose useful headers
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set(
    "Access-Control-Expose-Headers",
    ["OpenAI-Processing-Ms","OpenAI-Organization","OpenAI-Version","OpenAI-Model","X-Request-Id"].join(", ")
  );
  rh.set("Cache-Control", "no-store");

  // WebSocket upgrade is handled transparently by OpenAI for HTTP endpoints;
  // for realtime ws, this file can be extended similarly to the JS fallback.
  return new Response(resp.body, {
    status: resp.status,
    statusText: resp.statusText,
    headers: rh,
  });
};