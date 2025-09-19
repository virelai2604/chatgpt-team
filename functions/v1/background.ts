export const onRequestPost: PagesFunction = async (ctx) => {
  const req = ctx.request;
  const upstream = new URL("https://api.openai.com/v1/responses");

  // start from incoming headers
  const out = new Headers(req.headers);

  // inject server-side credentials if missing
  const env = (ctx.env ?? {}) as any;
  if (!out.get("authorization") && env.OPENAI_KEY) out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  if (!out.get("openai-organization") && env.OPENAI_ORG_ID) out.set("openai-organization", env.OPENAI_ORG_ID);
  if (!out.get("openai-project") && env.OPENAI_PROJECT) out.set("openai-project", env.OPENAI_PROJECT);

  // Responses endpoint does NOT need assistants beta
  out.delete("openai-beta");

  const ct = req.headers.get("content-type") || "";
  if (ct.includes("multipart/form-data")) {
    const form = await req.formData();
    if (!form.has("background")) form.append("background", "true");
    return fetch(upstream, { method: "POST", headers: out, body: form });
  }

  let body:any = {};
  try { body = await req.json(); } catch {}
  if (!body || typeof body !== "object") body = {};
  if (body.background === undefined) body.background = true;

  out.set("content-type", "application/json");
  return fetch(upstream, { method: "POST", headers: out, body: JSON.stringify(body) });
};
