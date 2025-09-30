import { onRequestGet as __v1_health_ts_onRequestGet } from "C:\\Tools\\ChatGpt Domain\\Cloudflare\\chatgpt-team\\functions\\v1\\health.ts"
import { onRequest as __v1___path___ts_onRequest } from "C:\\Tools\\ChatGpt Domain\\Cloudflare\\chatgpt-team\\functions\\v1\\[[path]].ts"
import { onRequestGet as __health_ts_onRequestGet } from "C:\\Tools\\ChatGpt Domain\\Cloudflare\\chatgpt-team\\functions\\health.ts"

export const routes = [
    {
      routePath: "/v1/health",
      mountPath: "/v1",
      method: "GET",
      middlewares: [],
      modules: [__v1_health_ts_onRequestGet],
    },
  {
      routePath: "/v1/:path*",
      mountPath: "/v1",
      method: "",
      middlewares: [],
      modules: [__v1___path___ts_onRequest],
    },
  {
      routePath: "/health",
      mountPath: "/",
      method: "GET",
      middlewares: [],
      modules: [__health_ts_onRequestGet],
    },
  ]