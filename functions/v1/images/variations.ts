export const onRequest: PagesFunction = async ({ request }) => {
  const upstream = "https://api.openai.com/v1/images/variations";
  const headers = new Headers(request.headers);
  headers.delete("content-length");
  const resp = await fetch(upstream, {
    method: "POST",
    headers,
    body: request.body
  });
  return new Response(resp.body, { status: resp.status, headers: resp.headers });
};
