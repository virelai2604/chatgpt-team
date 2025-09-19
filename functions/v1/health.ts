export const onRequestGet: PagesFunction = async ({ env, request }) => {
  const origin = new URL(request.url).origin;
  const body = {
    ok: true,
    now: new Date().toISOString(),
    origin,
    relay: "/v1/*",
    env: {
      OPENAI_KEY: !!env.OPENAI_KEY,
      OPENAI_ORG_ID: !!env.OPENAI_ORG_ID,
      OPENAI_PROJECT: !!env.OPENAI_PROJECT,
      OPENAI_BETA: env.OPENAI_BETA ?? null
    }
  };
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*"
    }
  });
};
