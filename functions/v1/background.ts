/**
 * Cloudflare Pages Function: /v1/background
 * Compatibility layer: forwards to OpenAI /v1/responses with background:true
 * Uses server-side injected headers (Authorization, OpenAI-Org/Project/Beta) handled by your [[path]].ts
 */
export const onRequestPost: PagesFunction = async (ctx) => {
  const req = ctx.request;
  const url = new URL(req.url);
  const upstream = new URL('https://api.openai.com/v1/responses');

  // Build outbound headers (preserve JSON/multipart; let [[path]].ts or CF inject auth headers)
  const outHeaders = new Headers(req.headers);
  // Normalize content-type for JSON case
  const ct = req.headers.get('content-type') || '';

  if (ct.includes('multipart/form-data')) {
    const form = await req.formData();
    if (!form.has('background')) form.append('background', 'true');
    return fetch(upstream.toString(), { method: 'POST', headers: outHeaders, body: form });
  }

  // Default: treat as JSON (or text -> try parse)
  let body: any = {};
  try { body = await req.json(); } catch { /* ignore; body stays {} */ }
  if (typeof body !== 'object' || body === null) body = {};
  if (body.background === undefined) body.background = true;

  return fetch(upstream.toString(), {
    method: 'POST',
    headers: (() => {
      const h = new Headers(outHeaders);
      h.set('content-type', 'application/json');
      return h;
    })(),
    body: JSON.stringify(body)
  });
};
