export const onRequest: PagesFunction = async (ctx) => {
  return await import("./chat_completions").then(mod => mod?.onRequest?.(ctx));
};
