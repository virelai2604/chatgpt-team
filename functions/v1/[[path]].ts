interface Env {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
}
type CFArgs = { request: Request; env: Env };

export async function onRequest({ request, env }: CFArgs): Promise<Response> {
  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, OpenAI-Organization, OpenAI-Beta, OpenAI-Project, X-Requested-With, Accept",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS",
        "Access-Control-Max-Age": "86400"
      }
    });
  }

  const inUrl = new URL(request.url);
  // Only relay OpenAI v1 endpoints; block moderations
  if (!inUrl.pathname.startsWith("/v1/")) return new Response("Not found", { status: 404 });
  if (inUrl.pathname.startsWith("/v1/moderations")) return new Response("Not found", { status: 404 });

  const upstream = "https://api.openai.com" + inUrl.pathname + inUrl.search;

  // Build upstream headers
  const fwd = new Headers(request.headers);
  fwd.set("Authorization", `Bearer ${env.OPENAI_KEY}`);
  if (env.OPENAI_ORG_ID) fwd.set("OpenAI-Organization", env.OPENAI_ORG_ID);

  // Allow client project scoping
  const clientProject = request.headers.get("OpenAI-Project");
  if (clientProject) fwd.set("OpenAI-Project", clientProject);

  // Assistants v2 beta header when needed
  const p = inUrl.pathname;
  if (p.startsWith("/v1/assistants") || p.startsWith("/v1/threads") || p.includes("/runs")) {
    fwd.set("OpenAI-Beta", "assistants=v2");
  }

  const init: RequestInit = {
    method: request.method,
    headers: fwd,
    body: (request.method === "GET" || request.method === "HEAD") ? undefined : request.body,
    redirect: "manual"
  };

  const resp = await fetch(upstream, init);

  // CORS + exposed headers
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set("Access-Control-Expose-Headers", "OpenAI-Processing-Ms, OpenAI-Organization, OpenAI-Version, OpenAI-Model, X-Request-Id");
  rh.set("Cache-Control", "no-store");

  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: rh });
}