// Cloudflare Pages Function to relay OpenAI API calls (TypeScript)
//
// This handler proxies all OpenAI /v1 endpoints while allowing
// optional organization, project and beta headers to be passed through
// from environment variables. It also disables the moderation endpoint
// entirely. If the incoming request is a WebSocket upgrade (for the
// realtime API) the connection is proxied bidirectionally.

import type { PagesFunction } from '@cloudflare/workers-types';

interface Env {
  /**
   * Primary secret key for authenticating against the OpenAI API.  This
   * property mirrors the legacy `OPENAI_KEY` and the more descriptive
   * `OPENAI_API_KEY`.  Either can be present at runtime and this worker
   * will use whichever is defined.
   */
  OPENAI_KEY?: string;
  OPENAI_API_KEY?: string;

  /**
   * Optional organization identifiers.  The OpenAI API accepts
   * `OpenAI-Organization` as a header; configuration variables can be
   * provided as `OPENAI_ORG_ID`, `OPENAI_ORG` or `OPENAI_ORGANIZATION`.
   */
  OPENAI_ORG_ID?: string;
  OPENAI_ORG?: string;
  OPENAI_ORGANIZATION?: string;

  /**
   * Optional project identifier to scope requests within the OpenAI
   * console.  When defined this will be forwarded via the
   * `OpenAI-Project` header.
   */
  OPENAI_PROJECT?: string;

  /**
   * Optional beta flag to enable experimental endpoints.  For example
   * `assistants=v2` enables the Assistants v2 API.
   */
  OPENAI_BETA?: string;

  /**
   * Overrides the default upstream base URL.  Normally requests are
   * forwarded to `https://api.openai.com`.  You may set `BASE` or
   * `BASE_URL` to point at a different upstream (e.g. a staging API).
   */
  BASE?: string;
  BASE_URL?: string;
}

/**
 * Proxy an HTTP request to OpenAI. Adds required auth header and optional
 * organization/project/beta headers. Streams the response through.
 */
async function proxyRequest(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  // Determine the upstream base.  Prefer explicit overrides (BASE_URL, BASE),
  // otherwise fall back to the OpenAI API.  Normalise by trimming trailing slashes.
  const upstreamBase = (env.BASE_URL || env.BASE || 'https://api.openai.com').replace(/\/+$/, '');
  const upstreamUrl = new URL(url.pathname + url.search, upstreamBase).toString();

  // Build outbound headers, starting from scratch to avoid leaking client
  // headers.  Resolve the API key from either OPENAI_API_KEY or OPENAI_KEY.
  const apiKey = env.OPENAI_API_KEY || env.OPENAI_KEY;
  const headers = new Headers();
  headers.set('Authorization', `Bearer ${apiKey}`);
  // Resolve organization header from multiple possible env names.
  const org = env.OPENAI_ORG_ID || env.OPENAI_ORG || env.OPENAI_ORGANIZATION;
  if (org) headers.set('OpenAI-Organization', org);
  if (env.OPENAI_PROJECT) headers.set('OpenAI-Project', env.OPENAI_PROJECT);
  if (env.OPENAI_BETA) headers.set('OpenAI-Beta', env.OPENAI_BETA);
  // Preserve content-type for non-GET/HEAD requests so upstream knows
  // how to parse the body.
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('content-type', contentType);

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: 'manual',
  };
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = request.body;
  }
  const upstreamResp = await fetch(upstreamUrl, init);
  // Merge upstream headers, allow exposing useful ones via CORS
  const respHeaders = new Headers(upstreamResp.headers);
  respHeaders.set('Access-Control-Allow-Origin', '*');
  respHeaders.set(
    'Access-Control-Expose-Headers',
    [
      'OpenAI-Processing-Ms',
      'OpenAI-Organization',
      'OpenAI-Version',
      'OpenAI-Model',
      'X-Request-Id',
    ].join(', ')
  );
  respHeaders.set('Cache-Control', 'no-store');
  return new Response(upstreamResp.body, {
    status: upstreamResp.status,
    statusText: upstreamResp.statusText,
    headers: respHeaders,
  });
}

/**
 * Upgrade and proxy a WebSocket to the OpenAI realtime API. This is used
 * for streaming audio and voice interactions. The environment variables
 * are still applied to the outbound connection.
 */
async function proxyWebSocket(request: Request, env: Env): Promise<Response> {
  const pair = new WebSocketPair();
  const clientSocket = pair[0];
  const serverSocket = pair[1];
  serverSocket.accept();
  try {
    const url = new URL(request.url);
    // Construct WebSocket upstream URL.  Prefer explicit overrides for the
    // base (BASE_URL, BASE) and convert http(s) to ws(s) accordingly.
    const rawBase = env.BASE_URL || env.BASE || 'https://api.openai.com';
    const parsed = new URL(rawBase);
    const upstreamWsUrl = `${parsed.protocol === 'http:' ? 'ws' : 'wss'}://${parsed.hostname}${url.pathname}${url.search}`;
    // Build authorization headers, resolving API key and optional org/project/beta flags
    const apiKey = env.OPENAI_API_KEY || env.OPENAI_KEY;
    const headers: Record<string, string> = {
      Authorization: `Bearer ${apiKey}`,
      Upgrade: 'websocket',
    };
    const org = env.OPENAI_ORG_ID || env.OPENAI_ORG || env.OPENAI_ORGANIZATION;
    if (org) headers['OpenAI-Organization'] = org;
    if (env.OPENAI_PROJECT) headers['OpenAI-Project'] = env.OPENAI_PROJECT;
    if (env.OPENAI_BETA) headers['OpenAI-Beta'] = env.OPENAI_BETA;
    const openaiResp = await fetch(upstreamWsUrl, { headers });
    const openaiSocket = openaiResp.webSocket;
    if (!openaiSocket) throw new Error('Failed to upgrade websocket');
    openaiSocket.accept();
    // Relay messages both directions
    openaiSocket.addEventListener('message', (ev) => serverSocket.send(ev.data));
    openaiSocket.addEventListener('close', () => serverSocket.close());
    openaiSocket.addEventListener('error', () => serverSocket.close());
    serverSocket.addEventListener('message', (ev) => openaiSocket.send(ev.data));
    serverSocket.addEventListener('close', () => openaiSocket.close());
    serverSocket.addEventListener('error', () => openaiSocket.close());
  } catch (err) {
    console.error('WebSocket error', err);
    serverSocket.close();
    return new Response('WebSocket connection failed', { status: 500 });
  }
  return new Response(null, { status: 101, webSocket: clientSocket });
}

export const onRequest: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  // Handle CORS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers':
          'Authorization, Content-Type, OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Requested-With, Accept',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS',
        'Access-Control-Max-Age': '86400',
      },
    });
  }
  const url = new URL(request.url);
  // Only proxy /v1/* paths; others return 404
  if (!url.pathname.startsWith('/v1/')) {
    return new Response('Not found', { status: 404 });
  }
  // Block moderation endpoint entirely
  if (url.pathname.startsWith('/v1/moderations')) {
    return new Response('Moderations endpoint disabled', { status: 403 });
  }
  // WebSocket upgrade handling for realtime endpoints
  if (request.headers.get('upgrade') === 'websocket') {
    return proxyWebSocket(request, env);
  }
  return proxyRequest(request, env);
};
