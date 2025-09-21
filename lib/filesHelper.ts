export function buildOpenAIHeaders(request: Request): Headers {
  const headers = new Headers();
  const auth = request.headers.get("Authorization");
  const org  = request.headers.get("OpenAI-Org");
  const proj = request.headers.get("OpenAI-Project");

  if (auth) headers.set("Authorization", auth);
  if (org)  headers.set("OpenAI-Org", org);

  // ✅ Only set project header if token is project-scoped
  if (proj && auth?.startsWith("Bearer sk-proj-")) {
    headers.set("OpenAI-Project", proj);
  }

  return headers;
}
