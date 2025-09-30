export async function onRequestPost(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const methodOverride = request.headers.get("x-method-override")?.toUpperCase();
  const finalMethod = methodOverride || "POST";

  let bodyJson;
  try { bodyJson = await request.json(); } catch {}

  const isStreaming = bodyJson?.stream === true;
  if (isStreaming) {
    const res = await fetch("https://api.openai.com" + url.pathname + url.search, {
      method: finalMethod,
      headers: {
        "Authorization": `Bearer ${env.OPENAI_API_KEY}`,
        "OpenAI-Organization": env.OPENAI_ORG_ID,
        "OpenAI-Beta": env.OPENAI_BETA,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(bodyJson)
    });
    return new Response(res.body, {
      status: res.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive"
      }
    });
  }

  const res2 = await fetch("https://api.openai.com" + url.pathname + url.search, {
    method: finalMethod,
    headers: {
      "Authorization": `Bearer ${env.OPENAI_API_KEY}`,
      "OpenAI-Organization": env.OPENAI_ORG_ID,
      "OpenAI-Beta": env.OPENAI_BETA,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(bodyJson)
  });

  return new Response(await res2.text(), {
    status: res2.status,
    headers: { "Content-Type": "application/json" }
  });
}
