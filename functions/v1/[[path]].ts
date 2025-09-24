import { httpRequestWithRetry } from "../../lib/httpClient";

import files from "./files";
import audioTranscription from "./audio_transcription";
import audioSpeech from "./audio_speech";
import imagesGenerations from "./images_generations";
import chatCompletions from "./chat_completions";
import assistants from "./assistants";
import threads from "./threads";
import runs from "./runs";
import vectorStores from "./vector_stores";
import vectorStoresSearch from "./vector_stores_search";
import vectorStoresFiles from "./vector_stores_files";

export const config = {
  runtime: "edge",
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // 🔁 Direct route handlers
    if (pathname.startsWith("/v1/files")) {
      return await files.httpRequestWithRetry(request);
    }
    if (pathname === "/v1/audio/transcriptions") {
      return await audioTranscription.httpRequestWithRetry(request);
    }
    if (pathname === "/v1/audio/speech") {
      return await audioSpeech.httpRequestWithRetry(request);
    }
    if (pathname === "/v1/images/generations") {
      return await imagesGenerations.httpRequestWithRetry(request);
    }
    if (pathname === "/v1/chat/completions") {
      return await chatCompletions.httpRequestWithRetry(request);
    }
    if (pathname === "/v1/responses") {
      // 🔧 ADD: responses endpoint routing (per YAML spec)
      return await chatCompletions.httpRequestWithRetry(request);
    }
    if (pathname.startsWith("/v1/assistants")) {
      return await assistants.httpRequestWithRetry(request);
    }
    if (pathname.startsWith("/v1/threads")) {
      if (pathname.includes("/runs")) return await runs.httpRequestWithRetry(request);
      return await threads.httpRequestWithRetry(request);
    }
    if (pathname.startsWith("/v1/vector_stores")) {
      if (pathname.match(/^\/v1\/vector_stores\/[^/]+\/search$/)) {
        return await vectorStoresSearch.httpRequestWithRetry(request);
      }
      if (pathname.match(/^\/v1\/vector_stores\/[^/]+\/files$/)) {
        return await vectorStoresFiles.httpRequestWithRetry(request);
      }
      return await vectorStores.httpRequestWithRetry(request);
    }

    // 🔒 Block moderations
    if (pathname.startsWith("/v1/moderations")) {
      return new Response(JSON.stringify({ error: "moderation blocked" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      });
    }

    // 🔁 Default passthrough to OpenAI upstream
    const upstream = "https://api.openai.com" + pathname + url.search;
    const headers = new Headers(request.headers);
    const relayHeaders = new Headers();

    for (const [k, v] of headers.entries()) {
      if (k.toLowerCase() !== "content-length") {
        relayHeaders.set(k, v);
      }
    }

    const init: RequestInit = {
      method: request.method,
      headers: relayHeaders,
      body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined,
    };

    const resp = await httpRequestWithRetry(upstream, init);
    return new Response(resp.body, {
      status: resp.status,
      headers: resp.headers,
    });
  },
};