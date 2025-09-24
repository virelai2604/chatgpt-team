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
      return new Response(JSON.stringify({ error: 'Invalid content type. Must be application/json.' }), { status: 400 });
    }

    const body = await request.json();
    const { input, model, voice, response_format } = body;

    if (!input || !model || !voice) {
      return new Response(JSON.stringify({ error: 'Missing required fields: input, model, voice' }), { status: 400 });
    }

    const upstream = 'https://api.openai.com/v1/audio/speech';

    const resp = await httpRequestWithRetry(upstream, {
      method: 'POST',
      headers: {
        Authorization: request.headers.get('Authorization') || '',
        'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
        'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input,
        model,
        voice,
        response_format: response_format || 'mp3',
      }),
    });

    return new Response(resp.body, {
      status: resp.status,
      headers: {
        'Content-Type': resp.headers.get('content-type') || 'audio/mpeg',
        'X-Relay-Origin': 'TTS',
      },
    });
  },
};


