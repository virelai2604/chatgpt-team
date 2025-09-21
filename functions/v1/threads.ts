import { httpRequestWithRetry } from "../../lib/httpClient";

export const onRequestPost: PagesFunction = async ({ request }) => {
  const body = await request.json();
  const isStreaming = body?.stream === true;
  const upstream = "https://api.openai.com/v1/threads";

  const headers = {
    Authorization: request.headers.get("Authorization") || "",
    "Content-Type": "application/json",
  };

  if (isStreaming) {
    const response = await fetch(upstream, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  }

  const response = await httpRequestWithRetry(upstream, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  const json = await response.json();
  return new Response(JSON.stringify(json), { status: response.status });
};
