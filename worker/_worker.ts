const modelsCache = new Set();
let modelSyncFailed = false;
let modelsReady = false;

async function syncModelList(apiKey) {
  console.log("🔄 syncModelList called");
  try {
    const res = await fetch("https://api.openai.com/v1/models", {
      headers: { Authorization: `Bearer ${apiKey}` }
    });
    console.log("✅ OpenAI responded");

    const text = await res.text();
    console.log("🔍 Response text:", text.slice(0, 200));

    const json = JSON.parse(text);
    if (Array.isArray(json.data)) {
      json.data.forEach((m) => modelsCache.add(m.id));
      modelsReady = true;
      console.log(`✅ Synced ${modelsCache.size} models`);
    } else {
      modelSyncFailed = true;
      console.warn("⚠️ Invalid model list structure");
    }
  } catch (err) {
    modelSyncFailed = true;
    console.error("❌ syncModelList failed:", err.message);
  }
}

function isModelSupported(model) {
  if (!modelsReady || modelSyncFailed) return true;
  return modelsCache.has(model);
}

async function guardedProxy(request, endpoint) {
  try {
    const raw = await request.text();
    const body = JSON.parse(raw);
    const model = body.model;

    if (!model || !isModelSupported(model)) {
      return new Response(JSON.stringify({
        error: {
          message: `Model '${model}' not supported.`,
          type: "model_not_supported",
          code: 501
        }
      }), { status: 501, headers: { "Content-Type": "application/json" } });
    }

    return fetch(endpoint, {
      method: "POST",
      headers: request.headers,
      body: raw
    });

  } catch (err) {
    return new Response("❌ Internal error: " + err.message, { status: 500 });
  }
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    if (!modelsReady && !modelSyncFailed) {
      const key = request.headers.get("Authorization")?.replace("Bearer ", "");
      if (key) await syncModelList(key);
    }

    if (pathname === "/v1/completions" || pathname === "/v1/chat/completions") {
      return guardedProxy(request, "https://api.openai.com" + pathname);
    }

    if (pathname === "/v1/realtime" && request.headers.get("Upgrade") === "websocket") {
      return fetch("wss://api.openai.com/v1/realtime", { headers: request.headers });
    }

    if (pathname.startsWith("/v1/")) {
      const proxyUrl = "https://chatgpt-team.pages.dev" + pathname + url.search;
      return fetch(proxyUrl, {
        method: request.method,
        headers: request.headers,
        body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined
      });
    }

    return new Response("Not Found", { status: 404 });
  }
};
