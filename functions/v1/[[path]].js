export async function onRequest({ request, env }) {
  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, OpenAI-Organization, OpenAI-Beta",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS"
      }
    });
  }

  const inUrl = new URL(request.url);
  if (!inUrl.pathname.startsWith("/v1/")) {
    return new Response("Not found", { status: 404 });
  }

  const upstream = "https://api.openai.com" + inUrl.pathname + inUrl.search;

  // Forward original headers, then inject auth/org/betas
  const headers = new Headers(request.headers);
  headers.set("Authorization", "Bearer " + env.OPENAI_KEY);
  if (env.OPENAI_ORG_ID) headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);

  // Assistants/Threads APIs require this beta header
  const p = inUrl.pathname;
  if (p.startsWith("/v1/assistants") || p.startsWith("/v1/threads") || p.includes("/runs")) {
    headers.set("OpenAI-Beta", "assistants=v2");
  }

  const init = {
    method: request.method,
    headers,
    body: (request.method === "GET" || request.method === "HEAD") ? undefined : request.body,
    redirect: "manual" // avoid auto-follow 307/308 with one-time-use body
  };

  const resp = await fetch(upstream, init);

  // Add permissive CORS on the way back
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set("Cache-Control", "no-store");

  return new Response(resp.body, {
    status: resp.status,
    statusText: resp.statusText,
    headers: rh
  });
}
