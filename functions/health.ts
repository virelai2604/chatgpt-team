type Env = {
  OPENAI_KEY?: string;
  OPENAI_PROJECT?: string;
  OPENAI_ORG_ID?: string;
  OPENAI_BETA?: string;
  CF_PAGES_URL?: string;
  CF_PAGES_BRANCH?: string;
  CF_PAGES_COMMIT_SHA?: string;
  CF_PAGES_COMMIT_MESSAGE?: string;
};

export const onRequest: PagesFunction<Env> = async ({ env, request }) => {
  const body = {
    ok: true,
    now: new Date().toISOString(),
    origin: new URL(request.url).origin,
    commit: {
      sha: env.CF_PAGES_COMMIT_SHA || null,
      message: env.CF_PAGES_COMMIT_MESSAGE || null,
      branch: env.CF_PAGES_BRANCH || null,
      previewUrl: env.CF_PAGES_URL || null,
    },
    env: {
      OPENAI_KEY: Boolean(env.OPENAI_KEY),
      OPENAI_PROJECT: Boolean(env.OPENAI_PROJECT),
      OPENAI_ORG_ID: Boolean(env.OPENAI_ORG_ID),
      OPENAI_BETA: env.OPENAI_BETA || null,
    },
  };

  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "Access-Control-Allow-Origin": "*",
    },
  });
};