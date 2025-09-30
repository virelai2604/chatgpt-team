export async function onRequestPost(context) {
  const { request, env } = context;
  const methodOverride = request.headers.get("x-method-override")?.toUpperCase();
  const finalMethod = methodOverride || "POST";
  const url = new URL(request.url);
  const target = "https://api.openai.com" + url.pathname + url.search;

  let bodyJson;
  try { bodyJson = await request.json(); } catch {}

  const isStreaming = bodyJson?.stream === true;
  const headers = {
    "Authorization": `Bearer ${env.OPENAI_API_KEY}`,
    "OpenAI-Organization": env.OPENAI_ORG_ID,
    "OpenAI-Beta": env.OPENAI_BETA,
    "Content-Type": "application/json"
  };

  const res = await fetch(target, {
    method: finalMethod,
    headers,
    body: JSON.stringify(bodyJson)
  });

  if (isStreaming) {
    return new Response(res.body, {
      status: res.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive"
      }
    });
  }

  return new Response(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" }
  });
}
