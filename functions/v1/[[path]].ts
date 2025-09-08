// functions/v1/[[path]].ts
type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // optional override, defaults to api.openai.com
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  // Health check
  if (url.pathname === "/health") {
    return new Response(JSON.stringify({ ok: true, ts: Date.now() }), {
      status: 200,
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
        "access-control-allow-origin": "*",
      },
    });
  }

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

  // (Optional) block moderations
  if (url.pathname.startsWith("/v1/moderations")) {
    return new Response(JSON.stringify({ error: { message: "blocked" } }), {
      status: 404,
      headers: {
        "content-type": "application/json",
        "access-control-allow-origin": "*",
        "cache-control": "no-store",
      },
    });
  }

  // Upstream target
  const base = env.BASE || "https://api.openai.com";
  const upstream = new URL(base + url.pathname + url.search);

  // Forward headers, inject server key if client didn't send one
  const out = new Headers(request.headers);
  if (!out.has("authorization") && env.OPENAI_KEY) {
    out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  }
  if (env.OPENAI_ORG_ID && !out.has("openai-organization")) {
    out.set("OpenAI-Organization", env.OPENAI_ORG_ID);
  }
  if (env.OPENAI_PROJECT && !out.has("openai-project")) {
    out.set("OpenAI-Project", env.OPENAI_PROJECT);
  }
  if (env.OPENAI_BETA) {
    out.set("OpenAI-Beta", env.OPENAI_BETA);
  }

  const init: RequestInit = {
    method: request.method,
    headers: out,
    redirect: "manual",
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
  };

  const resp = await fetch(upstream.toString(), init);
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set(
    "Access-Control-Expose-Headers",
    "OpenAI-Processing-Ms, OpenAI-Organization, OpenAI-Version, OpenAI-Model, X-Request-Id"
  );
  rh.set("Cache-Control", "no-store");

  return new Response(resp.body, {
    status: resp.status,
    statusText: resp.statusText,
    headers: rh,
  });
};
