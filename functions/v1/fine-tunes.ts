export const onRequest: PagesFunction = async () => {
  return new Response(JSON.stringify({
    error: "This endpoint (/v1/fine-tunes) is deprecated. Use /v1/fine_tuning/jobs instead."
  }), {
    status: 410,
    headers: { "content-type": "application/json" }
  });
};
