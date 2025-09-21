type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;
  BASE?: string; // default https://api.openai.com
};

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: cors() });
  }

  if (!url.pathname.startsWith("/v1/")) {
    return new Response("Not Found", { status: 404, headers: cors() });
  }

  if (url.pathname.startsWith("/v1/moderations")) {
    return json({ error: { message: "blocked" } }, 404, cors());
  }

  const base = (env.BASE || "https://api.openai.com").replace(/\/$/, "");
  const upstreamUrl = base + url.pathname + url.search;

  const out = new Headers(request.headers);
  if (!out.get("authorization") && env.OPENAI_KEY) {
    out.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  }
  if (env.OPENAI_ORG_ID) out.set("openai-organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT) out.set("openai-project", env.OPENAI_PROJECT);
  if (env.OPENAI_BETA) out.set("openai-beta", env.OPENAI_BETA);

  for (const h of ["host","content-length","connection","transfer-encoding","keep-alive","upgrade"]) {
    out.delete(h);
  }

  const method = request.method.toUpperCase();
  const ct = request.headers.get("content-type") || "";
  const isMultipart = ct.includes("multipart/form-data");

  let init: RequestInit;
  if (isMultipart) {
    const inForm = await request.formData();
    const outForm = new FormData();
    for (const [k, v] of inForm.entries()) outForm.append(k, v as any);

    init = { method, headers: out, body: outForm, redirect: "manual" };
  } else {
    init = { method, headers: out, body: (method === "GET" || method === "HEAD") ? undefined : request.body, redirect: "manual" };
  }

  const resp = await fetch(upstreamUrl, init);
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set("Access-Control-Expose-Headers", "OpenAI-Organization, OpenAI-Project, OpenAI-Beta, X-Request-Id");
  rh.set("Cache-Control", "no-store");

  return new Response(resp.body, { status: resp.status, headers: rh });
};

function cors(): Record<string,string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Authorization,Content-Type,OpenAI-Organization,OpenAI-Project,OpenAI-Beta,Accept",
    "Cache-Control": "no-store"
  };
}

function json(data: unknown, status = 200, headers: Record<string,string> = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: new Headers({ "content-type": "application/json; charset=utf-8", ...headers })
  });
}
