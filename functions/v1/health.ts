export const onRequestGet: PagesFunction = async (ctx) => {
  const { request, env } = ctx;
  const origin = new URL(request.url).origin;
  return new Response(JSON.stringify({
    ok: true,
    now: new Date().toISOString(),
    origin,
    relay: "/v1/*",
    env: {
      OPENAI_KEY: !!env.OPENAI_KEY,
      OPENAI_PROJECT: !!env.OPENAI_PROJECT,
      OPENAI_ORG_ID: !!env.OPENAI_ORG_ID,
      OPENAI_BETA: env.OPENAI_BETA ?? null
    }
  }, null, 2), { headers: { "content-type": "application/json; charset=utf-8" }});
};
