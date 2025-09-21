export async function fetchWithRetry(
  url: string,
  init: RequestInit,
  retries = 3,
  timeoutMs = 10000
): Promise<Response> {
  let attempt = 0;
  while (attempt < retries) {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), timeoutMs);
      const response = await fetch(url, { ...init, signal: controller.signal });
      clearTimeout(id);
      if (response.status < 500 || response.status === 429) {
        return response;
      }
    } catch (_) {}
    const backoff = 2 ** attempt * 300;
    await new Promise((r) => setTimeout(r, backoff));
    attempt++;
  }
  return new Response("Retry limit exceeded", { status: 504 });
}

export const httpRequestWithRetry = fetchWithRetry;
