type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string;
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Requested-With, Accept",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS",
        "Access-Control-Max-Age": "86400",
      },
    });
  }

  if (!url.pathname.startsWith("/v1/")) return new Response("Not found", { status: 404 });
  if (url.pathname.startsWith("/v1/moderations")) return new Response("Moderations endpoint disabled", { status: 403 });

  const upstream = new URL(url.pathname + url.search, env.BASE || "https://api.openai.com").toString();

  const out = new Headers();
  // Use concatenation to avoid PowerShell here-string issues
  out.set("Authorization", "Bearer " + env.OPENAI_KEY);

  const ct = request.headers.get("content-type");
  if (ct) out.set("content-type", ct);
  if (env.OPENAI_ORG_ID) out.set("OpenAI-Organization", env.OPENAI_ORG_ID);

  const clientProject = request.headers.get("OpenAI-Project");
  if (clientProject) out.set("OpenAI-Project", clientProject);
  else if (env.OPENAI_PROJECT) out.set("OpenAI-Project", env.OPENAI_PROJECT);

  if (env.OPENAI_BETA) out.set("OpenAI-Beta", env.OPENAI_BETA);
  const p = url.pathname;
  if ((p.startsWith("/v1/assistants") || p.startsWith("/v1/threads") || p.includes("/runs")) && !out.has("OpenAI-Beta")) {
    out.set("OpenAI-Beta", "assistants=v2");
  }

  const init: RequestInit = {
    method: request.method,
    headers: out,
    redirect: "manual",
    body: (request.method === "GET" || request.method === "HEAD") ? undefined : request.body,
  };

  const resp = await fetch(upstream, init);
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set("Access-Control-Expose-Headers", "OpenAI-Processing-Ms, OpenAI-Organization, OpenAI-Version, OpenAI-Model, X-Request-Id");
  rh.set("Cache-Control", "no-store");

  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: rh });
};