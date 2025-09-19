export const onRequestPost: PagesFunction = async (ctx) => {
  const { request, env } = ctx;
  const upstream = new URL("https://api.openai.com/v1/responses");
  const out = new Headers(request.headers);
  out.delete("openai-beta"); // Responses doesn't require assistants beta
  if (!out.get("authorization") && env.OPENAI_KEY) out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  if (env.OPENAI_ORG_ID && !out.has("openai-organization")) out.set("openai-organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT && !out.has("openai-project")) out.set("openai-project", env.OPENAI_PROJECT);

  const ct = request.headers.get("content-type") || "";
  if (ct.includes("multipart/form-data")) {
    const form = await request.formData();
    if (!form.has("background")) form.append("background","true");
    return fetch(upstream, { method:"POST", headers: out, body: form });
  }
  let body:any = {}; try { body = await request.json(); } catch {}
  if (!body || typeof body !== "object") body = {};
  if (body.background === undefined) body.background = true;
  out.set("content-type","application/json");
  return fetch(upstream, { method:"POST", headers: out, body: JSON.stringify(body) });
};
