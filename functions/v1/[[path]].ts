/* Cloudflare Pages catch-all proxy for OpenAI Platform.
   - Supports: /v1/... (Responses, Assistants v2, Files, Images, Audio, Models, Realtime pass-through)
   - Auto-injects OpenAI-Beta: assistants=v2 for assistants/threads/runs
   - Optional model family allowlist via env MODEL_FAMILY_ALLOWLIST_REGEX
   - Falls back to env.OPENAI_API_KEY if Authorization header is absent
*/

export interface Env {
  OPENAI_API_KEY?: string;
  OPENAI_ORGANIZATION?: string;  // preferred key name
  OPENAI_ORG?: string;           // alias
  OPENAI_PROJECT?: string;
  OPENAI_BETA?: string;          // default beta header if you want to force it
  BASE?: string;                 // override upstream (default https://api.openai.com)
  MODEL_FAMILY_ALLOWLIST_REGEX?: string; // e.g. ^(gpt-5(|-chat-latest|-mini|-nano)|gpt-4\.1(|-mini|-nano)|gpt-4o(|-mini)|o3(-pro)?|o4-mini|text-embedding-3(|-small|-large)|gpt-image-1|whisper-1|gpt-4o-(transcribe|mini-transcribe)|tts-1(|-hd)|gpt-4o-mini-tts|gpt-realtime.*)$
}

export const onRequest: PagesFunction<Env> = async (ctx) => {
  const { request, env } = ctx;
  const params: any = (ctx as any).params || {};
  const path = (params.path ?? "").toString(); // "models", "responses", "assistants", etc.

  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders(request) });
  }
  if (!path) {
    return json(400, { error: { message: "Missing path after /v1/" } });
  }

  // Build upstream URL using env.BASE or default
  const upstreamBase = (env.BASE || "https://api.openai.com").replace(/\/+$/, "");
  const inUrl = new URL(request.url);
  const url = new URL(`${upstreamBase}/v1/${path}`);
  for (const [k, v] of inUrl.searchParams) {
    url.searchParams.append(k, v);
  }

  // Prepare headers for the outgoing request
  const headers = new Headers(request.headers);

  // Provide Authorization header if missing using server-side key
  if (!headers.has("authorization")) {
    if (!env.OPENAI_API_KEY) {
      return json(401, { error: { message: "Missing Authorization header and OPENAI_API_KEY is not configured." } });
    }
    headers.set("authorization", `Bearer ${env.OPENAI_API_KEY}`);
  }

  // Normalize organisation and project identifiers
  const org =
    headers.get("openai-organization") ||
    headers.get("openai-org") ||
    env.OPENAI_ORGANIZATION ||
    env.OPENAI_ORG;
  if (org) headers.set("OpenAI-Organization", org);
  const project = headers.get("openai-project") || env.OPENAI_PROJECT;
  if (project) headers.set("OpenAI-Project", project);

  // Inject Assistants v2 beta header for assistants endpoints
  if (/^(assistants|threads|runs)/.test(path)) {
    headers.set("OpenAI-Beta", "assistants=v2");
  } else if (env.OPENAI_BETA && !headers.has("openai-beta")) {
    headers.set("OpenAI-Beta", env.OPENAI_BETA);
  }

  // Remove hop-by-hop headers that should not be forwarded
  [
    "host",
    "content-length",
    "cf-connecting-ip",
    "cf-ipcountry",
    "cf-ray",
    "connection",
    "x-forwarded-for",
    "x-forwarded-proto",
  ].forEach((h) => headers.delete(h));

  // Optionally enforce model family allowlist on JSON payloads
  if (
    headers.get("content-type")?.includes("application/json") &&
    env.MODEL_FAMILY_ALLOWLIST_REGEX
  ) {
    const text = await request.clone().text();
    try {
      const payload = JSON.parse(text);
      const modelName = payload?.model;
      if (typeof modelName === "string") {
        const re = new RegExp(env.MODEL_FAMILY_ALLOWLIST_REGEX);
        if (!re.test(modelName)) {
          return json(400, {
            error: {
              message: `Model "${modelName}" is not permitted by relay policy.`,
              type: "invalid_model",
              param: "model",
            },
          });
        }
      }
      const upstream = await fetch(url.toString(), {
        method: request.method,
        headers,
        body: text,
      });
      return passthrough(upstream);
    } catch {
      // fall through to default pass-through when JSON parsing fails
    }
  }

  // Default pass-through: forward the request with streaming body
  const upstream = await fetch(url.toString(), {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
  });
  return passthrough(upstream);
};

function json(status: number, data: unknown): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...corsHeaders(),
    },
  });
}

function corsHeaders(_req?: Request): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers":
      "Authorization,Content-Type,OpenAI-Organization,OpenAI-Project,OpenAI-Beta",
  };
}

function passthrough(res: Response): Response {
  const headers = new Headers(res.headers);
  const cors = corsHeaders();
  Object.entries(cors).forEach(([k, v]) => headers.set(k, v));
  return new Response(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers,
  });
}