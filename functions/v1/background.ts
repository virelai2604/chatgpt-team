export const onRequestPost: PagesFunction = async ({ request, env }) => {
  const b = await (async () => { try { return await request.json(); } catch { return {}; }})();
  const body = { ...(b || {}), background: true };
  const h = new Headers({ "content-type": "application/json", "authorization": `Bearer ${env.OPENAI_KEY}` });
  if (env.OPENAI_ORG_ID)    h.set("openai-organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT_ID) h.set("openai-project", env.OPENAI_PROJECT_ID);
  const r = await fetch("https://api.openai.com/v1/responses", { method:"POST", headers:h, body: JSON.stringify(body) });
  return new Response(r.body, { status: r.status, headers: r.headers });
};
