export interface Env {
  OPENAI_API_KEY: string;
  OPENAI_ORG?: string;
  OPENAI_ORGANIZATION?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE_URL?: string; // e.g. http://127.0.0.1:8787/v1 in dev, https://api.openai.com/v1 in prod
}

export const onRequest: PagesFunction<Env> = async (ctx) => {
  try {
    const { request, env } = ctx;
    const url = new URL(request.url);

    // 1) Local health & smoke route
    if (url.pathname === '/v1/models' && request.method === 'GET') {
      // Keep it simple: static OK response for local smoke tests
      const payload = {
        object: 'list',
        data: [
          { id: 'gpt-4o', object: 'model', created: 1715367049, owned_by: 'system' },
          { id: 'gpt-4.1', object: 'model', created: 1744316542, owned_by: 'system' },
          { id: 'gpt-5', object: 'model', created: 1754425777, owned_by: 'system' }
        ]
      };
      return new Response(JSON.stringify(payload), {
        headers: { 'content-type': 'application/json' }
      });
    }

    // 2) Proxy everything else to your upstream (OpenAI or relay target)
    const upstreamBase = env.BASE_URL || 'https://api.openai.com/v1';
    const target = new URL(upstreamBase);
    target.pathname = url.pathname; // keep /v1/...
    target.search = url.search;

    // Build outgoing request
    const headers = new Headers(request.headers);
    // Ensure Authorization is present when proxying to OpenAI
    if (!headers.get('authorization') && env.OPENAI_API_KEY) {
      headers.set('authorization', `Bearer ${env.OPENAI_API_KEY}`);
    }
    if (env.OPENAI_BETA) headers.set('OpenAI-Beta', env.OPENAI_BETA);
    if (env.OPENAI_PROJECT) headers.set('OpenAI-Project', env.OPENAI_PROJECT);
    if (env.OPENAI_ORGANIZATION || env.OPENAI_ORG) {
      headers.set('OpenAI-Organization', env.OPENAI_ORGANIZATION || env.OPENAI_ORG!);
    }

    const proxied = new Request(target.toString(), {
      method: request.method,
      headers,
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body
    });

    const res = await fetch(proxied);
    // Always return a Response
    return new Response(res.body, {
      status: res.status,
      statusText: res.statusText,
      headers: res.headers
    });
  } catch (err: any) {
    // Never drop the response
    return new Response(
      JSON.stringify({ error: { message: err?.message || 'Unhandled error' } }),
      { status: 500, headers: { 'content-type': 'application/json' } }
    );
  }
};
