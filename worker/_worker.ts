export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
// --- Realtime WS Patch Start ---
if (url.pathname.startsWith("/v1/realtime")) {
  if (request.headers.get("Upgrade") !== "websocket") {
    return new Response("Expected WebSocket", { status: 426 });
  }
  const { socket, response } = Deno.upgradeWebSocket(request);
  socket.onopen = () => {
    socket.send(JSON.stringify({ type: "system", message: "Realtime WS connected" }));
  };
  socket.onmessage = (event) => {
    socket.send(JSON.stringify({ type: "echo", data: event.data }));
  };
  return response;
}
// --- Realtime WS Patch End ---
    const method = request.method;
    const pathname = url.pathname;

    if (pathname.startsWith("/v1/realtime")) {
      // Your WS logic stays here...
      return new Response("Realtime WS not yet implemented.", { status: 501 });
    }

    if (pathname.startsWith("/v1/")) {
      const proxyUrl = "https://chatgpt-team.pages.dev" + pathname + url.search;
      const resp = await fetch(proxyUrl, {
        method,
        headers: request.headers,
        body: method !== "GET" && method !== "HEAD" ? request.body : undefined,
      });
      return new Response(resp.body, {
        status: resp.status,
        headers: resp.headers,
      });
    }

    return new Response("Not Found", { status: 404 });
  }
}

