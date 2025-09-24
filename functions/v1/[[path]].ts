export const onRequest: PagesFunction = async ({ request }) => {
  const url = new URL(request.url);
  const pathname = url.pathname;

  // Block moderation intentionally
  if (pathname === "/v1/moderations" || pathname.startsWith("/v1/moderations/")) {
    return new Response(JSON.stringify({
      error: "This endpoint is blocked by policy."
    }), {
      status: 403,
      headers: { "content-type": "application/json" }
    });
  }

  // Default passthrough to upstream OpenAI API
  const upstream = "https://api.openai.com" + pathname + url.search;
  const relayedHeaders = new Headers(request.headers);
  relayedHeaders.delete("content-length");
  const resp = await fetch(upstream, {
    method: request.method,
    headers: relayedHeaders,
    body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined
  });

  return new Response(resp.body, {
    status: resp.status,
    headers: resp.headers,
  });
};
