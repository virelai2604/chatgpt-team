export const onRequest = async ({ request, env }) => {
  const inUrl = new URL(request.url);
  const upstream = `https://api.openai.com${inUrl.pathname}${inUrl.search}`;

  const headers = new Headers(request.headers);
  headers.set("Authorization", `Bearer ${env.OPENAI_KEY}`);
  if (env.OPENAI_ORG_ID) headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);

  // Pass method, headers, and body through unchanged
  return fetch(upstream, {
    method: request.method,
    headers,
    body: request.body,
  });
};