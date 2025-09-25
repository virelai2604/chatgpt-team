import { fetchWithRetry } from "../../lib/httpClient";
import { buildOpenAIHeaders } from "../../lib/filesHelper";

export const onRequest: PagesFunction = async (context) => {
  const { request } = context;
  const url = new URL(request.url);
  const method = request.method.toUpperCase();
  const pathname = url.pathname;

  if (method === "POST" && pathname === "/v1/chat/completions") {
    const contentType = request.headers.get("Content-Type") || "";
    if (!contentType.includes("application/json")) {
      return new Response("Invalid Content-Type, expecting application/json", { status: 400 });
    }
    const bodyJson = await request.json();
    const { model, messages, stream } = bodyJson;

    const headers = buildOpenAIHeaders(request);
    headers.set("Content-Type", "application/json");

    const openaiRequest = {
      model,
      messages,
      stream: stream === true
    };

    const openaiResponse = await fetchWithRetry("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: headers,
      body: JSON.stringify(openaiRequest)
    });

    if (stream === true) {
      const responseStream = openaiResponse.body;
      if (!responseStream) {
        return new Response("No response body for streaming", { status: 502 });
      }
      return new Response(responseStream, {
        status: openaiResponse.status,
        headers: openaiResponse.headers
      });
    } else {
      const text = await openaiResponse.text();
      return new Response(text, {
        status: openaiResponse.status,
        headers: openaiResponse.headers
      });
    }
  }

  return new Response("Not Found", { status: 404 });
};
