import type { PagesFunction } from '../[[path]]';

export const onRequest: PagesFunction = async ({ request }) => {
  const url = new URL(request.url);
  const method = request.method.toUpperCase();

  const upstreamPath = url.pathname.replace(/^\/v1\//, '');
  const upstreamUrl = `https://api.openai.com/v1/${upstreamPath}${url.search}`;

  const headers = new Headers(request.headers);
  const body =
    method !== "GET" && method !== "HEAD"
      ? request.body
      : undefined;

  const resp = await fetch(upstreamUrl, {
    method,
    headers,
    body
  });

  return new Response(resp.body, {
    status: resp.status,
    headers: resp.headers
  });
};