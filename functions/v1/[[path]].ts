export const onRequest: PagesFunction = async (ctx) => {
  const req = ctx.request;
  const url = new URL(req.url);
  const path = url.pathname.replace(/\/+$/, "");
  const method = req.method.toUpperCase();

  // 1) Block moderations outright (policy)
  if (path === "/v1/moderations") {
    return new Response(JSON.stringify({ error: "blocked" }), {
      status: 404, headers: { "content-type":"application/json", "access-control-allow-origin":"*" }
    });
  }

  // Build upstream headers & gate OpenAI-Beta to Assistants/Threads only
  const env = (ctx.env ?? {}) as any;
  const buildHeaders = (target: string) => {
    const h = new Headers(req.headers);
    h.delete("host"); h.delete("content-length");
    if (!h.get("authorization") && env.OPENAI_KEY) h.set("authorization", `Bearer ${env.OPENAI_KEY}`);
    if (!h.get("openai-organization") && env.OPENAI_ORG_ID) h.set("openai-organization", env.OPENAI_ORG_ID);
    if (!h.get("openai-project") && env.OPENAI_PROJECT) h.set("openai-project", env.OPENAI_PROJECT);
    const isAssistants = /^\/v1\/(assistants|threads|runs)/.test(target);
    if (isAssistants) {
      const val = env.OPENAI_BETA || "assistants=v2";
      h.set("openai-beta", val.includes("assistants=") ? val : "assistants=v2");
    } else {
      h.delete("openai-beta");
    }
    return h;
  };

  const passthrough = async (target: string) => {
    const upstream = new URL("https://api.openai.com" + target);
    const headers = buildHeaders(target);
    const ct = req.headers.get("content-type") || "";
    if (method === "GET" || method === "DELETE") return fetch(upstream, { method, headers });
    if (ct.includes("multipart/form-data")) {
      const form = await req.formData();
      return fetch(upstream, { method, headers, body: form });
    }
    let body: any; try { body = await req.text(); } catch {}
    return fetch(upstream, { method, headers, body });
  };

  const forwardJSON = async (target: string, bodyObj: any) => {
    const upstream = new URL("https://api.openai.com" + target);
    const headers = buildHeaders(target);
    headers.set("content-type", "application/json");
    return fetch(upstream, { method: "POST", headers, body: JSON.stringify(bodyObj) });
  };

  // 2) Legacy → modern shims
  if (path === "/v1/completions" && method === "POST") {
    let b:any = {}; try { b = await req.json(); } catch {}
    const input = Array.isArray(b.prompt) ? b.prompt.join("\n") : (b.prompt ?? "");
    const model = (typeof b.model === "string" && b.model.trim()) ? b.model : "gpt-4o-mini";
    const mapped:any = { model, input };
    if (typeof b.max_tokens === "number") mapped.max_output_tokens = b.max_tokens; // modern cap
    return forwardJSON("/v1/responses", mapped);
  }

  if (path === "/v1/edits" && method === "POST") {
    let b:any = {}; try { b = await req.json(); } catch {}
    const instruction = b.instruction ?? "";
    const input = b.input ?? "";
    const model = (typeof b.model === "string" && b.model.trim()) ? b.model : "gpt-4o-mini";
    const composed = `Apply the following instruction to the text.\nInstruction:\n${instruction}\n\nText:\n${input}`;
    return forwardJSON("/v1/responses", { model, input: composed });
  }

  // 3) Default pass-through
  return passthrough(path);
};
