export const onRequest: PagesFunction = async (context) => {
  return new Response(JSON.stringify({ ok: true, service: "health", ts: Date.now() }), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*"
    }
  });
};
