export const onRequest: PagesFunction = async ({ request, env }) => {
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

  const upstream = `https://api.openai.com${inUrl.pathname}${inUrl.search}`;

  // Preserve original headers (keeps multipart boundaries)
  const outHeaders = new Headers(request.headers);
  outHeaders.set("Authorization", `Bearer ${env.OPENAI_KEY}`);
  if (env.OPENAI_ORG_ID) outHeaders.set("OpenAI-Organization", env.OPENAI_ORG_ID);

  // Clone original request to keep streaming/multipart intact
  const upstreamReq = new Request(upstream, {
    method: request.method,
    headers: outHeaders,
    body: request.body,
    // @ts-ignore: helps in some dev runtimes
    duplex: "half"
  });

  const resp = await fetch(upstreamReq);

  // Add permissive CORS back
  const respHeaders = new Headers(resp.headers);
  respHeaders.set("Access-Control-Allow-Origin", "*");

  return new Response(resp.body, {
    status: resp.status,
    statusText: resp.statusText,
    headers: respHeaders
  });
};
