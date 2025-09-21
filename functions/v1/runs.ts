export const config = {
  runtime: 'edge',
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;
    const pathname = url.pathname;

    // POST /v1/threads/{thread_id}/runs
    const runsMatch = pathname.match(/^\/v1\/threads\/([^\/]+)\/runs$/);
    if (method === 'POST' && runsMatch) {
      const thread_id = runsMatch[1];
      const body = await request.json();
      const resp = await httpRequestWithRetry(`https://api.openai.com/v1/threads/${thread_id}/runs`, {
        method: 'POST',
        headers: {
          Authorization: request.headers.get('Authorization') || '',
          'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
          'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      if (body?.stream === true) {
        return new Response(resp.body, {
          status: resp.status,
          headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-store',
            'X-Relay-Origin': 'runs-stream',
          },
        });
      }
      const json = await resp.json();
      return new Response(JSON.stringify(json), { status: resp.status });
    }

    const runGetMatch = pathname.match(/^\/v1\/threads\/([^\/]+)\/runs\/([^\/]+)$/);
    if (method === 'GET' && runGetMatch) {
      const thread_id = runGetMatch[1];
      const run_id = runGetMatch[2];
      const resp = await httpRequestWithRetry(`https://api.openai.com/v1/threads/${thread_id}/runs/${run_id}`, {
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

    return new Response(JSON.stringify({ error: 'Not found in runs' }), { status: 404 });
  },
};


