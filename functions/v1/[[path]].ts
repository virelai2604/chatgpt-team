import files from "./files";
import { httpRequestWithRetry } from "../../lib/httpClient";
import audioTranscription from "./audio_transcription";
import { httpRequestWithRetry } from "../../lib/httpClient";
import audioSpeech from "./audio_speech";
import { httpRequestWithRetry } from "../../lib/httpClient";
import imagesGenerations from "./images_generations";
import { httpRequestWithRetry } from "../../lib/httpClient";
import chatCompletions from "./chat_completions";
import { httpRequestWithRetry } from "../../lib/httpClient";
import assistants from "./assistants";
import { httpRequestWithRetry } from "../../lib/httpClient";
import threads from "./threads";
import { httpRequestWithRetry } from "../../lib/httpClient";
import runs from "./runs";
import { httpRequestWithRetry } from "../../lib/httpClient";
import vectorStores from "./vector_stores";
import { httpRequestWithRetry } from "../../lib/httpClient";
import vectorStoresSearch from "./vector_stores_search";
import { httpRequestWithRetry } from "../../lib/httpClient";
import vectorStoresFiles from "./vector_stores_files";
import { httpRequestWithRetry } from "../../lib/httpClient";

export const config = {
  runtime: "edge",
};

export default {
  async httpRequestWithRetry(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;

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

    if (pathname.startsWith("/v1/assistants")) {
      return await assistants.httpRequestWithRetry(request);
    }

    if (pathname.startsWith("/v1/threads")) {
      if (pathname.includes("/runs")) return await runs.httpRequestWithRetry(request);
      return await threads.httpRequestWithRetry(request);
    }

    if (pathname.startsWith("/v1/vector_stores")) {
      if (pathname.match(/^\/v1\/vector_stores\/[^\/]+\/search$/)) {
        return await vectorStoresSearch.httpRequestWithRetry(request);
      }
      if (pathname.match(/^\/v1\/vector_stores\/[^\/]+\/files$/)) {
        return await vectorStoresFiles.httpRequestWithRetry(request);
      }
      return await vectorStores.httpRequestWithRetry(request);
    }

    if (pathname.startsWith("/v1/moderations")) {
      return new Response(JSON.stringify({ error: "moderation blocked" }), {
        status: 403,
      });
    }

    const upstream = "https://api.openai.com" + pathname + url.search;
    const headers = new Headers(request.headers);
    const relayHeaders = new Headers();
    for (const [k, v] of headers.entries()) {
      if (!["content-length"].includes(k.toLowerCase())) {
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



