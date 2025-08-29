import { onRequestPost as __v1_chat_completions_ts_onRequestPost } from "C:\\Tools\\ChatGpt Domain\\Cloudflare\\chatgpt-team\\functions\\v1\\chat\\completions.ts"

export const routes = [
    {
      routePath: "/v1/chat/completions",
      mountPath: "/v1/chat",
      method: "POST",
      middlewares: [],
      modules: [__v1_chat_completions_ts_onRequestPost],
    },
  ]