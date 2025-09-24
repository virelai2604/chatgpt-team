import { httpRequestWithRetry } from "../../lib/httpClient";
import files from "./files";
import audioTranscription from "./audio_transcription";
import audioSpeech from "./audio_speech";
import imagesGenerations from "./images_generations";
import chatCompletions from "./chat_completions";
import completions from "./completions";
import edits from "./edits";
import assistants from "./assistants";
import threads from "./threads";
import runs from "./runs";
import vectorStores from "./vector_stores";
import vectorStoresSearch from "./vector_stores_search";
import vectorStoresFiles from "./vector_stores_files";

export const config = { runtime: "edge" };

export const onRequest: PagesFunction = async ({ request }) => {
  const url = new URL(request.url);
  const pathname = url.pathname;

  // === Explicit Moderation Block
  if (pathname.startsWith("/v1/moderations")) {
    return new Response(JSON.stringify({ error: "moderation blocked" }), {
      status: 403,
      headers: { "content-type": "application/json" },
    });
  }

  // === Serve Known Routes First
  if (pathname === "/v1/audio/transcriptions") {
    return audioTranscription.onRequest?.({ request });
  }
  if (pathname === "/v1/audio/speech") {
    return audioSpeech.onRequest?.({ request });
  }
  if (pathname === "/v1/images/generations") {
    return imagesGenerations.onRequest?.({ request });
  }
  if (pathname === "/v1/chat/completions") {
    return chatCompletions.onRequest?.({ request });
  }
  if (pathname === "/v1/completions") {
    return completions.onRequest?.({ request });
  }
  if (pathname === "/v1/edits") {
    return edits.onRequest?.({ request });
  }
  if (pathname === "/v1/responses") {
    return chatCompletions.onRequest?.({ request }); // alias
  }

  // === Assistants v2 Logic
  if (pathname.startsWith("/v1/assistants")) {
    return assistants.onRequest?.({ request });
  }
  if (pathname.startsWith("/v1/threads/") && pathname.includes("/runs/") && pathname.includes("/steps")) {
    return runs.onRequest?.({ request }); // run step fetch
  }
  if (pathname.startsWith("/v1/threads/") && pathname.includes("/runs")) {
    return runs.onRequest?.({ request }); // run launch or fetch
  }
  if (pathname.startsWith("/v1/threads")) {
    return threads.onRequest?.({ request });
  }

  // === Vector search handlers
  if (/^\/v1\/vector_stores\/[^/]+\/search$/.test(pathname)) {
    return vectorStoresSearch.onRequest?.({ request });
  }
  if (/^\/v1\/vector_stores\/[^/]+\/files$/.test(pathname)) {
    return vectorStoresFiles.onRequest?.({ request });
  }
  if (pathname.startsWith("/v1/vector_stores")) {
    return vectorStores.onRequest?.({ request });
  }

  if (pathname.startsWith("/v1/files")) {
    return files.onRequest?.({ request });
  }

  // === Final Fallback: Pass-through upstream
  const upstreamUrl = "https://api.openai.com" + pathname + url.search;
  const relayHeaders = new Headers(request.headers);

  // Strip content-length + force auth fallback
  relayHeaders.delete("content-length");

  // Inject auth header if omitted but env has fallback
  if (!relayHeaders.has("authorization") && typeof process !== "undefined" && process.env.OPENAI_KEY) {
    relayHeaders.set("authorization", `Bearer ${process.env.OPENAI_KEY}`);
  }

  const upstreamInit: RequestInit = {
    method: request.method,
    headers: relayHeaders,
    body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined,
  };

  const response = await httpRequestWithRetry(upstreamUrl, upstreamInit);
  return new Response(response.body, {
    status: response.status,
    headers: response.headers,
  });
};