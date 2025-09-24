export const onRequest: PagesFunction = async ({ request }) => {
  const upstream = "https://api.openai.com/v1/completions";
  const headers = new Headers(request.headers);
  headers.delete("content-length");
  const forward = await fetch(upstream, {
    method: request.method,
    headers,
    body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined,
  });
  return new Response(forward.body, {
    status: forward.status,
    headers: forward.headers,
  });
};
