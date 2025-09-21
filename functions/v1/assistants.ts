export const config = {
  runtime: 'edge',
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;
    const pathname = url.pathname;

    if (method === 'POST' && pathname === '/v1/assistants') {
      const body = await request.json();
      const resp = await httpRequestWithRetry('https://api.openai.com/v1/assistants', {
        method: 'POST',
        headers: {
          Authorization: request.headers.get('Authorization') || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      const json = await resp.json();
      return new Response(JSON.stringify(json), { status: resp.status });
    }

    return new Response(JSON.stringify({ error: 'Not found in assistants' }), { status: 404 });
  },
};


