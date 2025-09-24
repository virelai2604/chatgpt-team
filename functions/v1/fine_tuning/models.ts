import type { PagesFunction } from '../[[path]]';

export const onRequest: PagesFunction = async ({ request }) => {
  const url = new URL(request.url);

  const upstreamUrl = 'https://api.openai.com/v1/fine_tuning/models' + url.search;

  const resp = await fetch(upstreamUrl, {
    method: 'GET',
    headers: request.headers
  });

  return new Response(resp.body, {
    status: resp.status,
    headers: resp.headers
  });
};