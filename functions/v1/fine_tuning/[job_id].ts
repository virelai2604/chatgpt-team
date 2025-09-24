import type { PagesFunction } from '../[[path]]';

export const onRequest: PagesFunction = async ({ request }) => {
  const url = new URL(request.url);
  const method = request.method.toUpperCase();

  const upstreamPath = url.pathname.replace(/^\/v1\/fine_tuning/, '');
  const upstreamUrl = `https://api.openai.com/v1/fine_tuning${upstreamPath}${url.search}`;

  const resp = await fetch(upstreamUrl, {
    method,
    headers: request.headers,
    body: method !== "GET" && method !== "HEAD" ? request.body : undefined
  });

  return new Response(resp.body, {
    status: resp.status,
    headers: resp.headers
  });
};