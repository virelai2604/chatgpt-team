export const config = {
  runtime: 'edge',
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405 });
    }

    const contentType = request.headers.get('content-type') || '';
    if (!contentType.includes('multipart/form-data')) {
      return new Response(JSON.stringify({ error: 'Invalid content type' }), { status: 400 });
    }

    const formData = await request.formData();
    const file = formData.get('file');
    const model = formData.get('model') || 'whisper-1';
    const response_format = formData.get('response_format') || 'json';
    const language = formData.get('language');

    if (!(file instanceof File)) {
      return new Response(JSON.stringify({ error: 'Missing or invalid file' }), { status: 400 });
    }

    const formRelay = new FormData();
    formRelay.append('file', file);
    formRelay.append('model', model);
    formRelay.append('response_format', response_format);
    if (language) {
      formRelay.append('language', language);
    }

    const resp = await httpRequestWithRetry('https://api.openai.com/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        Authorization: request.headers.get('Authorization') || '',
        'OpenAI-Org': request.headers.get('OpenAI-Org') || '',
        'OpenAI-Project': request.headers.get('OpenAI-Project') || '',
      },
      body: formRelay,
    });

    const json = await resp.json();
    return new Response(JSON.stringify(json), { status: resp.status });
  },
};


