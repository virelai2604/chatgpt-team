import { Configuration } from "../tools/sdk-typescript/dist/configuration.js";
import { DefaultApi } from "../tools/sdk-typescript/dist/api.js";

const config = new Configuration({
  apiKey: process.env.OPENAI_API_KEY
});

const api = new DefaultApi(config);

async function main() {
  // ⚠ Ensure this matches your OpenAPI schema's auto-generated method
  const result = await api.v1ModelsGet();
  console.log("✅ Models:", result.data.map(m => m.id));
}

main().catch(err => {
  console.error("❌ SDK test failed:", err.message || err);
});
