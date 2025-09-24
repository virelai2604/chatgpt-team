/*
  SDK‑format fine‑tuning handlers file
  Supports:
    POST /v1/fine_tuning/jobs
    GET  /v1/fine_tuning/jobs
    GET  /v1/fine_tuning/jobs/{id}
    POST /v1/fine_tuning/jobs/{id}/cancel
    GET  /v1/fine_tuning/models
*/
export async function handleFineTuning(request: Request, pathname: string, method: string): Promise<Response> {
  const upstreamBase = 'https://api.openai.com/v1/fine_tuning';
  const segments = pathname.split('/').filter(Boolean); // split and remove empty
  // segments example: ['v1','fine_tuning','jobs'], ['v1','fine_tuning','jobs','{id}'], etc.

  // remove 'v1' prefix
  if (segments[0] === 'v1') {
    segments.shift();
  }

  // segments[0] should now === 'fine_tuning'
  if (segments[0] !== 'fine_tuning') {
    return new Response('Not Found', { status: 404 });
  }

  // handle models listing: /fine_tuning/models
  if (segments.length === 2 && segments[1] === 'models' && method === 'GET') {
    const resp = await fetch(upstreamBase + '/models' + new URL(request.url).search, {
      method: 'GET',
      headers: request.headers
    });
    return new Response(resp.body, { status: resp.status, headers: resp.headers });
  }

  // handle jobs endpoints
  if (segments.length >= 2 && segments[1] === 'jobs') {
    let target = upstreamBase + '/jobs';
    if (segments.length === 3 && segments[2]) {
      // /jobs/{id}
      target += '/' + segments[2];
    }
    if (segments.length === 4 && segments[3] === 'cancel' && method === 'POST') {
      // /jobs/{id}/cancel
      target += '/' + segments[2] + '/cancel';
    }
    const resp = await fetch(target + new URL(request.url).search, {
      method: method,
      headers: request.headers,
      body: method !== 'GET' && method !== 'HEAD' ? request.body : undefined
    });
    return new Response(resp.body, { status: resp.status, headers: resp.headers });
  }

  return new Response('Invalid fine_tuning path', { status: 400 });
}
