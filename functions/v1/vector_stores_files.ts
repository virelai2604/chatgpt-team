export const config = {
  runtime: 'edge',
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;
    const pathname = url.pathname;

    const vsFilesMatch = pathname.match(/^\/v1\/vector_stores\/([^\/]+)\/files$/);
    if ((method === 'POST' || method === 'GET') && vsFilesMatch) {
      const vs_id = vsFilesMatch[1];

      if (method === 'POST') {
        // Attach file by ID to vector store
        const body = await request.json();
        const resp = await httpRequestWithRetry(`https://api.openai.com/v1/vector_stores/${vs_id}/files`, {
          method: 'POST',
          headers: {
            Authorization: request.headers.get('Authorization') || '',
            'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
            'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body)
        });
        const json = await resp.json();
        return new Response(JSON.stringify(json), { status: resp.status });
      }

      if (method === 'GET') {
        const resp = await httpRequestWithRetry(`https://api.openai.com/v1/vector_stores/${vs_id}/files`, {
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
    }

    return new Response(JSON.stringify({ error: 'Not found vector_stores files' }), { status: 404 });
  },
};


