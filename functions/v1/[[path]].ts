export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const override = request.headers.get("x-method-override")?.toUpperCase();
  const method = override || request.method;
  if (url.pathname.startsWith("/v1/moderations")) {
    return new Response(JSON.stringify({ error: "blocked" }), { status: 403 });
  }
  const target = "https://api.openai.com" + url.pathname + url.search;
  const headers = new Headers(request.headers);
  headers.set("Authorization", `Bearer ${env.OPENAI_API_KEY}`);
  if (env.OPENAI_ORG_ID) headers.set("OpenAI-Organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_BETA) headers.set("OpenAI-Beta", env.OPENAI_BETA);
  let bodyJson;
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    try {
      bodyJson = await request.json();
  const isStreaming = bodyJson?.stream === true;
  if (isStreaming) {
    const res = await fetch(target, {
      method: finalMethod,
      headers,
      body: JSON.stringify(bodyJson),
    });
    return new Response(res.body, {
      status: res.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive"
      }
    });
  }
    } catch {}
    if (override === "GET" && bodyJson) {
      for (const [key, value] of Object.entries(bodyJson)) {
        url.searchParams.append(key, value?.toString?.() ?? "");
      }
    }
    );
      return new Response(res.body, {
        status: res.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Connection": "keep-alive"
        }
      });
    }
  }
  const body = ["POST", "PUT", "PATCH", "DELETE"].includes(method) ? JSON.stringify(bodyJson) : undefined;
  const res = await fetch(target, { method, headers, body });
  return new Response(res.body, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("Content-Type") ?? "application/json"
    }
  });
}

