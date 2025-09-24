import type { PagesFunction } from "../[[path]]";
import { httpRequestWithRetry } from "../../../lib/httpClient";

export const onRequest: PagesFunction = async ({ request }) => {
  if (request.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    const form = await request.formData();
    const file = form.get("file");
    const purpose = form.get("purpose");

    if (!(file instanceof File)) {
      return new Response("Missing `file` field (must be File)", { status: 400 });
    }
    if (typeof purpose !== "string") {
      return new Response("Missing `purpose` field", { status: 400 });
    }

    const body = new FormData();
    body.set("file", file);
    body.set("purpose", purpose);

    const headers = new Headers();
    const auth = request.headers.get("Authorization");
    const org = request.headers.get("OpenAI-Org");
    const proj = request.headers.get("OpenAI-Project");

    if (auth) headers.set("Authorization", auth);
    if (org)  headers.set("OpenAI-Org", org);
    if (proj && auth?.startsWith("Bearer sk-proj-")) {
      headers.set("OpenAI-Project", proj);
    }

    const resp = await httpRequestWithRetry("https://api.openai.com/v1/files", {
      method: "POST",
      headers,
      body
    });

    return new Response(resp.body, { status: resp.status, headers: resp.headers });
  } catch (err) {
    return new Response("❌ File relay failed\n" + (err instanceof Error ? err.message : err), {
      status: 500
    });
  }
};