type Env = {
  OPENAI_KEY: string;
  OPENAI_ORG_ID?: string;
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;   // e.g., "assistants=v2, realtime=v1"
  BASE?: string;          // upstream override; default https://api.openai.com
};

function cors(): Record<string,string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS",
    "Access-Control-Allow-Headers": "Authorization,Content-Type,OpenAI-Organization,OpenAI-Project,OpenAI-Beta,X-Requested-With,Accept",
    "Access-Control-Expose-Headers": "OpenAI-Processing-Ms,OpenAI-Organization,OpenAI-Project,OpenAI-Beta,OpenAI-Model,X-Request-Id",
    "Cache-Control": "no-store"
  };
}
function j(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "content-type":"application/json; charset=utf-8", ...cors() }});
}

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const url = new URL(request.url);
  const method = request.method.toUpperCase();
  const path = url.pathname.replace(/\/+$/, "");

  if (method === "OPTIONS") return new Response(null, { status: 204, headers: cors() });
  if (!path.startsWith("/v1/")) return new Response("Not Found", { status: 404, headers: cors() });

  // Policy: block Moderations in this relay
  if (path === "/v1/moderations") return j({ error: { message: "blocked" } }, 404);

  // NEW: Pages is HTTP-only; realtime must go via the WS Worker
  if (path === "/v1/realtime") {
    return j({ ok:false, error:"WebSocket upgrade required", hint:"Use your Worker /v1/realtime endpoint (workers.dev route)" }, 426);
  }

  // ===== Legacy shims =====
  const forwardJSON = async (target: string, bodyObj: any) => {
    const upstream = new URL((env.BASE || "https://api.openai.com").replace(/\/$/,"") + target);
    const headers = buildHeaders(target);
    headers.set("content-type","application/json");
    return fetch(upstream, { method:"POST", headers, body: JSON.stringify(bodyObj), redirect: "manual" });
  };

  if (path === "/v1/completions" && method === "POST") {
    let b:any = {}; try { b = await request.json(); } catch {}
    const input = Array.isArray(b.prompt) ? b.prompt.join("\n") : (b.prompt ?? "");
    const model = (typeof b.model === "string" && b.model.trim()) ? b.model : "gpt-4o-mini";
    const mapped:any = { model, input };
    if (typeof b.max_tokens === "number") mapped.max_output_tokens = b.max_tokens;
    return forwardJSON("/v1/responses", mapped);
  }

  if (path === "/v1/edits" && method === "POST") {
    let b:any = {}; try { b = await request.json(); } catch {}
    const instruction = b.instruction ?? "";
    const input = b.input ?? "";
    const model = (typeof b.model === "string" && b.model.trim()) ? b.model : "gpt-4o-mini";
    const composed = `Apply the following instruction to the text.\nInstruction:\n${instruction}\n\nText:\n${input}`;
    return forwardJSON("/v1/responses", { model, input: composed });
  }

  // ===== Pass-through for everything else under /v1/* =====
  const upstreamUrl = (env.BASE || "https://api.openai.com").replace(/\/$/,"") + path + url.search;
  const out = buildHeaders(path);
  for (const h of ["host","content-length","connection","transfer-encoding","keep-alive","upgrade"]) out.delete(h);

  const ct = request.headers.get("content-type") || "";
  let init: RequestInit = { method, headers: out, redirect: "manual" };

  if (method !== "GET" && method !== "HEAD") {
    if (ct.includes("multipart/form-data")) {
      const inForm = await request.formData();
      const outForm = new FormData();
      for (const [k,v] of inForm.entries()) outForm.append(k, v as any);
      // When sending FormData, restrict headers to allowed upstream
      const h = new Headers();
      if (out.get("authorization"))        h.set("authorization", out.get("authorization")!);
      if (out.get("openai-organization"))  h.set("openai-organization", out.get("openai-organization")!);
      if (out.get("openai-project"))       h.set("openai-project", out.get("openai-project")!);
      if (out.get("openai-beta"))          h.set("openai-beta", out.get("openai-beta")!);
      init = { method, headers: h, body: outForm, redirect: "manual" };
    } else {
      init.body = request.body;
    }
  }

  const resp = await fetch(upstreamUrl, init);
  const rh = new Headers(resp.headers);
  rh.set("Access-Control-Allow-Origin", "*");
  rh.set("Access-Control-Expose-Headers", "OpenAI-Processing-Ms,OpenAI-Organization,OpenAI-Project,OpenAI-Beta,OpenAI-Model,X-Request-Id");
  rh.set("Cache-Control", "no-store");
  return new Response(resp.body, { status: resp.status, statusText: resp.statusText, headers: rh });

  function buildHeaders(targetPath: string): Headers {
    const h = new Headers(request.headers);
    if (!h.get("authorization") && env.OPENAI_KEY) h.set("authorization", `Bearer ${env.OPENAI_KEY}`);
    if (env.OPENAI_ORG_ID && !h.has("openai-organization")) h.set("openai-organization", env.OPENAI_ORG_ID);
    if (env.OPENAI_PROJECT && !h.has("openai-project"))     h.set("openai-project", env.OPENAI_PROJECT);

    const assistantsLike = /^\/v1\/(assistants|threads|runs)/.test(targetPath);
    if (assistantsLike) {
      const beta = (env.OPENAI_BETA || "assistants=v2").trim();
      h.set("openai-beta", beta.includes("assistants=") ? beta : "assistants=v2");
    } else {
      h.delete("openai-beta");
    }
    return h;
  }
};
