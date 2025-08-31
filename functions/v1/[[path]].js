export async function onRequest({ request, env }) {
  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, OpenAI-Organization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS"
      }
    });
  }

  const inUrl = new URL(request.url);
  if (!inUrl.pathname.startsWith("/v1/")) {
    return new Response("Not found", { status: 404 });
  }

  const upstream = "https://api.openai.com" + inUrl.pathname + inUrl.search;

  // forward original headers, then inject auth/org
  const headers = new Headers(request.headers);
  headers.set("Authorization", "Bearer " + env.OPENAI_KEY);
  if (env.OPENAI_ORG_ID) headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);

  const init = { method: request.method, headers };
  if (request.method !== "GET" && request.method !== "HEAD") init.body = request.body;

  const resp = await fetch(upstream, init);

  // add permissive CORS on the way back
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");

  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: rh });
}
