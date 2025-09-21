export const config = {
  runtime: 'edge',
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;
    const pathname = url.pathname;

    // POST /v1/vector_stores
    if (method === 'POST' && pathname === '/v1/vector_stores') {
      const body = await request.json();
      const resp = await httpRequestWithRetry('https://api.openai.com/v1/vector_stores', {
        method: 'POST',
        headers: {
          Authorization: request.headers.get('Authorization') || '',
          'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
          'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      const json = await resp.json();
      return new Response(JSON.stringify(json), { status: resp.status });
    }

    const vsMatch = pathname.match(/^\/v1\/vector_stores\/([^\/]+)$/);
    if (method === 'GET' && vsMatch) {
      const vs_id = vsMatch[1];
      const resp = await httpRequestWithRetry(`https://api.openai.com/v1/vector_stores/${vs_id}`, {
        method: 'GET',
        headers: {
          Authorization: request.headers.get('Authorization') || '',
          'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
          'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
        },
      });
      const json = await resp.json();
      return new Response(JSON.stringify(json), { status: resp.status });
    }

    if (method === 'GET' && pathname === '/v1/vector_stores') {
      const resp = await httpRequestWithRetry('https://api.openai.com/v1/vector_stores', {
        method: 'GET',
        headers: {
          Authorization: request.headers.get('Authorization') || '',
          'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
          'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
        },
      });
      const json = await resp.json();
      return new Response(JSON.stringify(json), { status: resp.status });
    }

    if (method === 'DELETE' && vsMatch) {
      const vs_id = vsMatch[1];
      const resp = await httpRequestWithRetry(`https://api.openai.com/v1/vector_stores/${vs_id}`, {
        method: 'DELETE',
        headers: {
          Authorization: request.headers.get('Authorization') || '',
          'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
          'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
        },
      });
      const json = await resp.json();
      return new Response(JSON.stringify(json), { status: resp.status });
    }

    return new Response(JSON.stringify({ error: 'Not found vector_stores' }), { status: 404 });
  },
};


