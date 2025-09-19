export const onRequestOptions: PagesFunction = async () => {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "authorization,content-type,openai-organization,openai-project",
      "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS"
    }
  });
};

export const onRequest: PagesFunction = async (ctx) => {
  const { request, env } = ctx;
  const url = new URL(request.url);
  const path = url.pathname;
  const method = request.method.toUpperCase();

  // Block moderations by policy
  if (path === "/v1/moderations") {
    return new Response(JSON.stringify({ error: "blocked by relay policy" }), {
      status: 404,
      headers: { "content-type": "application/json", "Access-Control-Allow-Origin": "*" }
    });
  }

  const buildHeaders = (target: string) => {
    const h = new Headers(request.headers);
    h.set("authorization", `Bearer ${env.OPENAI_KEY}`);
    if (env.OPENAI_ORG_ID)    h.set("openai-organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT_ID) h.set("openai-project", env.OPENAI_PROJECT_ID);

    // Beta header only where needed (Assistants v2)
    const needsAssistV2 =
      target.startsWith("/v1/assistants") ||
      target.startsWith("/v1/threads")    ||
      target.startsWith("/v1/runs"); // future-safe

    if (needsAssistV2) { h.set("openai-beta", "assistants=v2"); }
    else { h.delete("openai-beta"); }

    // Always allow cross-origin
    h.set("origin", url.origin);
    return h;
  };

  const passthrough = async (target: string) => {
    const upstream = new URL("https://api.openai.com" + target);
    const headers  = buildHeaders(target);
    const ct = request.headers.get("content-type") || "";

    if (method === "GET" || method === "DELETE") {
      return fetch(upstream, { method, headers });
    }
    if (ct.includes("multipart/form-data")) {
      const form = await request.formData();
      return fetch(upstream, { method, headers, body: form });
    }
    let body: any; try { body = await request.text(); } catch {}
    return fetch(upstream, { method, headers, body });
  };

  const forwardJSON = async (target: string, bodyObj: any) => {
    const upstream = new URL("https://api.openai.com" + target);
    const headers  = buildHeaders(target);
    headers.set("content-type","application/json");
    return fetch(upstream, { method:"POST", headers, body: JSON.stringify(bodyObj) });
  };

  // Legacy shim: /v1/completions -> /v1/responses
  if (path === "/v1/completions" && method === "POST") {
    let b:any = {}; try { b = await request.json(); } catch {}
    const input = Array.isArray(b.prompt) ? b.prompt.join("\n") : (b.prompt ?? "");
    const model = (typeof b.model === "string" && b.model.trim()) ? b.model : "gpt-4o-mini";
    const mapped:any = { model, input };
    if (typeof b.max_tokens === "number") mapped.max_output_tokens = b.max_tokens;
    return forwardJSON("/v1/responses", mapped);
  }

  // Legacy shim: /v1/edits -> /v1/responses
  if (path === "/v1/edits" && method === "POST") {
    let b:any = {}; try { b = await request.json(); } catch {}
    const instruction = b.instruction ?? "";
    const input = b.input ?? "";
    const model = (typeof b.model === "string" && b.model.trim()) ? b.model : "gpt-4o-mini";
    const composed = `Apply the following instruction to the text.\nInstruction:\n${instruction}\n\nText:\n${input}`;
    return forwardJSON("/v1/responses", { model, input: composed });
  }

  // Default pass-through
  if (!path.startsWith("/v1/")) {
    return new Response(JSON.stringify({ error: "only /v1/* allowed" }), {
      status: 404, headers: { "content-type":"application/json", "Access-Control-Allow-Origin": "*" }
    });
  }
  const resp = await passthrough(path);
  // mirror CORS on way out
  const oh = new Headers(resp.headers);
  oh.set("Access-Control-Allow-Origin", "*");
  return new Response(resp.body, { status: resp.status, headers: oh });
};
