export const onRequest: PagesFunction = async ({ params }) => {
  const assistantId = params.assistant_id;
  return new Response(JSON.stringify({ id: assistantId, object: "assistant", status: "ok" }), {
    headers: { "content-type": "application/json" },
    status: 200
  });
};
