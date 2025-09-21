// test_realtime.js
import WebSocket from "ws";

const url = "wss://chatgpt-team-realtime.virelai.workers.dev/v1/realtime?model=gpt-4o-realtime-preview";

const headers = {
  "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
  "OpenAI-Org": process.env.OPENAI_ORG_ID,
  "OpenAI-Project": process.env.OPENAI_PROJECT
};

const ws = new WebSocket(url, { headers });

ws.on("open", () => {
  console.log("✅ Connected to Realtime Worker");
  ws.send(JSON.stringify({ type: "ping", data: "relay-test" }));
});

ws.on("message", (msg) => {
  console.log("🔊 Message:", msg.toString());
});

ws.on("error", (err) => {
  console.error("❌ Error:", err);
});

ws.on("close", () => {
  console.log("🔌 Connection closed");
});

