/* Universal proxy for /v1/* with:
 * - Moderations hard-block
 * - Beta header gating (assistants only)
 * - Legacy shims:
 *   /v1/completions -> /v1/responses
 *   /v1/edits       -> /v1/responses
 */
export const onRequest: PagesFunction = async (ctx) => {
  const req = ctx.request;
  const url = new URL(req.url);
  const path = url.pathname.replace(/\/+$/, ""); // strip trailing slash
  const method = req.method.toUpperCase();

  // 1) Block moderations by policy
  if (path === "/v1/moderations") {
    return new Response(JSON.stringify({ error: { message: "blocked" }}), {
      status: 404, headers: { "content-type": "application/json", "access-control-allow-origin": "*" }
    });
  }

  // Utility: build upstream headers safely and gate OpenAI-Beta
  const buildHeaders = (targetPath: string) => {
    const h = new Headers(req.headers);
    // CORS + hop-by-hop
    h.delete("host"); h.delete("content-length");

    // Inject server-side secrets if not provided (Pages env)
    const env = ctx.env as any || {};
    if (!h.get("authorization") && env.OPENAI_KEY) h.set("authorization", `Bearer ${env.OPENAI_KEY}`);
    if (!h.get("openai-organization") && env.OPENAI_ORG_ID) h.set("openai-organization", env.OPENAI_ORG_ID);
    if (!h.get("openai-project") && env.OPENAI_PROJECT) h.set("openai-project", env.OPENAI_PROJECT);

    // Gate OpenAI-Beta: only attach for Assistants family
    const needsAssistantsBeta = /^\/v1\/(assistants|threads|runs)/.test(targetPath);
    if (needsAssistantsBeta) {
      const v = env.OPENAI_BETA || "assistants=v2";
      h.set("openai-beta", v.includes("assistants=") ? v : "assistants=v2");
    } else {
      h.delete("openai-beta"); // do not leak beta to Responses/Chat/etc.
    }
    return h;
  };

  // Helper: forward JSON body
  const forwardJSON = async (targetPath: string, bodyObj: any) => {
    const upstream = new URL(`https://api.openai.com${targetPath}`);
    const headers = buildHeaders(targetPath);
    headers.set("content-type", "application/json");
    return fetch(upstream, { method: "POST", headers, body: JSON.stringify(bodyObj) });
  };

  // Helper: pass-through (JSON or multipart)
  const passthrough = async (targetPath: string) => {
    const upstream = new URL(`https://api.openai.com${targetPath}`);
    const headers = buildHeaders(targetPath);
    const ct = req.headers.get("content-type") || "";
    if (method === "GET" || method === "DELETE") {
      return fetch(upstream, { method, headers });
    }
    if (ct.includes("multipart/form-data")) {
      const form = await req.formData();
      return fetch(upstream, { method, headers, body: form });
    }
    // default: JSON/text
    let body: any = undefined;
    try { body = await req.text(); } catch {}
    return fetch(upstream, { method, headers, body });
  };

  // 2) Legacy shim: /v1/completions  -> /v1/responses (prompt -> input)
  if (path === "/v1/completions" && method === "POST") {
    let body:any = {};
    try { body = await req.json(); } catch {}
    // Map legacy -> modern
    const input = Array.isArray(body.prompt) ? body.prompt.join("\n") : (body.prompt ?? "");
    const model = (typeof body.model === "string" && body.model.trim()) ? body.model : "gpt-4o-mini";
    const max_output_tokens = body.max_tokens ?? undefined;
    const mapped = { model, input };
    if (typeof max_output_tokens === "number") (mapped as any).max_output_tokens = max_output_tokens;
    return forwardJSON("/v1/responses", mapped);
  }

  // 3) Legacy shim: /v1/edits -> /v1/responses (instruction+input -> input)
  if (path === "/v1/edits" && method === "POST") {
    let body:any = {};
    try { body = await req.json(); } catch {}
    const instruction = body.instruction ?? "";
    const input = body.input ?? "";
    const composed = `Apply the following instruction to the text.\nInstruction:\n${instruction}\n\nText:\n${input}`;
    const model = (typeof body.model === "string" && body.model.trim()) ? body.model : "gpt-4o-mini";
    return forwardJSON("/v1/responses", { model, input: composed });
  }

  // 4) Everything else: pass-through to upstream
  return passthrough(path);
};
