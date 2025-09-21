import { httpRequestWithRetry } from "../../../lib/httpClient";
import { formDataFromReadableStream } from "../../../lib/formData";

export const onRequest: PagesFunction = async ({ request }) => {
  if (request.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const contentType = request.headers.get("content-type") || "";
  if (!contentType.includes("multipart/form-data")) {
    return new Response("Expected multipart/form-data", { status: 400 });
  }

  const formData = await formDataFromReadableStream(request);

  // Extract headers conditionally (BIFL safe)
  const headers = new Headers();
  const auth = request.headers.get("Authorization") || "";
  const org  = request.headers.get("OpenAI-Org");
  const proj = request.headers.get("OpenAI-Project");

  if (auth) headers.set("Authorization", auth);
  if (org)  headers.set("OpenAI-Org", org);
  if (proj && auth.startsWith("Bearer sk-proj-")) {
    headers.set("OpenAI-Project", proj);
  }

  const response = await httpRequestWithRetry("https://api.openai.com/v1/files", {
    method: "POST",
    headers,
    body: formData
  });

  return response;
};
