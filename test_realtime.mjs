import WebSocket from "ws";

const url = "wss://chatgpt-team-realtime.pages.dev/v1/realtime";
const ws = new WebSocket(url, {
  headers: {
    Authorization: `Bearer ${process.env.OPENAI_KEY}`,
    "OpenAI-Org": process.env.OPENAI_ORG_ID
  }
});

ws.on("open", () => {
  console.log("[✅] Connected to /v1/realtime");
  ws.send(JSON.stringify({ type: "ping", data: "hello from test client" }));
});

ws.on("message", (data) => {
  console.log("[📩] Received:", data.toString());
});

ws.on("close", (code, reason) => {
  console.log(`[❌] Closed: ${code} ${reason}`);
  process.exit(0);
});

ws.on("error", (err) => {
  console.error("[⚠️] Error:", err.message);
  process.exit(1);
});
