export const onRequestPost: PagesFunction = async ({ request }) => {
  const body = await request.json();
  // echo input for now; implement logic later
  return new Response(JSON.stringify({ vector_store_id: "vs_123", ...body }), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
};
