export const onRequestPost = async (ctx) => {
  const upstream = await fetch(
    "https://api.openai.com/v1/chat/completions",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${ctx.env.OPENAI_KEY}`,
        "OpenAI-Organization": "org-BE0YNlrYbCShFGQxMkW2f0fU"
      },
      body: await ctx.request.text()
    }
  );
  return new Response(upstream.body, upstream);
};
