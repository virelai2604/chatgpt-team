export const config = {
  runtime: 'edge',
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405 });
    }

    const contentType = request.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      return new Response(JSON.stringify({ error: 'Invalid content type' }), { status: 400 });
    }

    const body = await request.json();
    const { prompt, model, n, size, response_format, user } = body;

    if (!prompt || !model) {
      return new Response(JSON.stringify({ error: 'Missing required fields: prompt, model' }), { status: 400 });
    }

    const upstream = 'https://api.openai.com/v1/images/generations';

    const resp = await httpRequestWithRetry(upstream, {
      method: 'POST',
      headers: {
        Authorization: request.headers.get('Authorization') || '',
        'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
        'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        model,
        n,
        size,
        response_format,
        user,
      }),
    });

    const json = await resp.json();
    return new Response(JSON.stringify(json), {
      status: resp.status,
      headers: {
        'Content-Type': 'application/json',
        'X-Relay-Origin': 'images/generations',
      },
    });
  },
};


