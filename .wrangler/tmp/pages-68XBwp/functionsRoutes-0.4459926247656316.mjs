import { onRequest as __v1___path___js_onRequest } from "C:\\Tools\\ChatGpt Domain\\Cloudflare\\chatgpt-team\\functions\\v1\\[[path]].js"

export const routes = [
    {
      routePath: "/v1/:path*",
      mountPath: "/v1",
      method: "",
      middlewares: [],
      modules: [__v1___path___js_onRequest],
    },
  ]