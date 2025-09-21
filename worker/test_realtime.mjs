import WebSocket from "ws";

const url = "wss://chatgpt-team-realtime.virelai.workers.dev/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17";
const ws = new WebSocket(url, { perMessageDeflate: false });

ws.on("open", () => {
  console.log("[client] open");
  const msg = {
    type: "response.create",
    response: { instructions: "Say pong once, then finish." }
  };
  ws.send(JSON.stringify(msg));
});

ws.on("message", (data) => {
  try {
    // Most server events are JSON; print compactly
    const t = typeof data === "string" ? data : data.toString("utf8");
    console.log("[server]", t);
  } catch {
    console.log("[server] (binary)", data.length, "bytes");
  }
});

// Exit after a short window so CI/smoke doesn't hang
setTimeout(() => {
  console.log("[client] closing");
  ws.close(1000, "done");
}, 5000);

ws.on("close", (code, reason) => {
  console.log("[client] closed:", code, reason?.toString());
  process.exit(0);
});

ws.on("error", (err) => {
  console.error("[client] error:", err);
  process.exit(1);
});