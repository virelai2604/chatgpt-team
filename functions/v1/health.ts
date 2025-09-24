export const onRequest: PagesFunction = async ({ request, env }) => {
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET, HEAD, OPTIONS",
        "access-control-allow-headers": "*",
        "cache-control": "no-store",
      },
    });
  }

  return new Response(JSON.stringify({
    ok: true,
    service: "health",
    ts: Date.now(),
    region: env.CF_REGION ?? "unknown"
  }), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*"
    },
  });
};