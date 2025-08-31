export const onRequest = async ({ request, env }) => {
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
  const upstream = "https://api.openai.com" + inUrl.pathname + inUrl.search;

  const headers = new Headers(request.headers);
  headers.set("Authorization", "Bearer " + env.OPENAI_KEY);
  if (env.OPENAI_ORG_ID) headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
  headers.delete("Host"); // never forward Host

  const method = request.method || "GET";
  const init = { method, headers };
  if (method !== "GET" && method !== "HEAD") init.body = request.body;

  try {
    const resp = await fetch(upstream, init);

    // Add CORS headers to upstream response
    const out = new Headers(resp.headers);
    out.set("Access-Control-Allow-Origin", "*");
    out.set("Access-Control-Allow-Headers", "Authorization, Content-Type, OpenAI-Organization");
    out.set("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");

    return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: out });
  } catch (err) {
    return new Response(JSON.stringify({ error: "upstream_fetch_failed", message: String(err) }), {
      status: 502,
      headers: {
        "content-type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, OpenAI-Organization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS"
      }
    });
  }
};
