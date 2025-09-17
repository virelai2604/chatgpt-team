type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string; // e.g., assistants=v2
  BASE?: string;        // default https://api.openai.com
};

function cors() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "*",
    "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "cache-control": "no-store"
  };
}
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...cors() }
  });
}

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);

  // CORS preflight
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors() });

  // Health (versioned)
  if (url.pathname === "/v1/health") {
    return json({
      ok: true, now: new Date().toISOString(), origin: url.origin, relay: "/v1/*",
      env: {
        OPENAI_KEY: !!env.OPENAI_KEY,
        OPENAI_PROJECT: !!env.OPENAI_PROJECT,
        OPENAI_ORG_ID: !!env.OPENAI_ORG_ID,
        OPENAI_BETA: env.OPENAI_BETA ?? null
      }
    });
  }

  // Policy: BLOCK moderation endpoint
  if (url.pathname.startsWith("/v1/moderations")) {
    return json({ error: { message: "blocked" } }, 404);
  }

  // WS must use the Worker
  if (url.pathname.startsWith("/v1/realtime")) {
    return json({ error: { message: "Use the realtime Worker (HTTP 426)" } }, 426);
  }

  if (!url.pathname.startsWith("/v1/")) return new Response("Not Found", { status: 404 });

  // Build upstream
  const base = (env.BASE || "https://api.openai.com").replace(/\/$/, "");
  const upstream = base + url.pathname + url.search;

  // Prepare headers
  const h = new Headers(request.headers);
  if (!h.has("authorization") && env.OPENAI_KEY) h.set("authorization", `Bearer ${env.OPENAI_KEY}`);
  if (env.OPENAI_ORG_ID && !h.has("openai-organization")) h.set("openai-organization", env.OPENAI_ORG_ID);
  if (env.OPENAI_PROJECT && !h.has("openai-project")) h.set("openai-project", env.OPENAI_PROJECT);
  if (env.OPENAI_BETA && !h.has("openai-beta")) h.set("openai-beta", env.OPENAI_BETA);
  for (const x of ["host","connection","keep-alive","transfer-encoding","upgrade","content-length"]) h.delete(x);

  const method = request.method.toUpperCase();
  const ct = request.headers.get("content-type") || "";
  const isMultipart = ct.includes("multipart/form-data");

  let body: BodyInit | null = null;
  if (["GET","HEAD"].includes(method)) {
    body = null;
  } else if (isMultipart) {
    const inForm = await request.formData();
    const outForm = new FormData();
    for (const [k, v] of inForm.entries()) outForm.append(k, v as any);
    body = outForm;
    h.delete("content-type"); // boundary set by fetch
  } else {
    body = request.body;
  }

  const resp = await fetch(upstream, { method, headers: h, body });
  const rh = new Headers(resp.headers);
  for (const [k,v] of Object.entries(cors())) rh.set(k, v as string);
  return new Response(resp.body, { status: resp.status, headers: rh });
};