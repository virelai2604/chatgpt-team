export const onRequest: PagesFunction = async () => {
  return new Response(JSON.stringify({
    error: "This endpoint (/v1/edits) has been deprecated. Please migrate to /v1/chat/completions."
  }), {
    status: 410,
    headers: { "content-type": "application/json" }
  });
};
