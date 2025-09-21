export const config = {
  runtime: "edge",
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;
    const pathname = url.pathname;

    const vsSearchMatch = pathname.match(/^\/v1\/vector_stores\/([^\/]+)\/search$/);
    if (method === "POST" && vsSearchMatch) {
      const vs_id = vsSearchMatch[1];
      const body = await request.json();
      // expected body: { query: string, optional filters: object, optional max_num_results: integer }
      const resp = await httpRequestWithRetry(`https://api.openai.com/v1/vector_stores/${vs_id}/search`, {
        method: "POST",
        headers: {
          Authorization: request.headers.get("Authorization") || "",
          "OpenAI-Org": request.headers.get("OpenAI-Org") || "",
          "OpenAI-Project": request.headers.get("OpenAI-Project") || "",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      const json = await resp.json();
      return new Response(JSON.stringify(json), { status: resp.status });
    }

    return new Response(JSON.stringify({ error: "Not found in vector_stores/search" }), { status: 404 });
  },
};


