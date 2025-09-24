import type { PagesFunction } from '../../../../../[[path]]';
export const onRequest: PagesFunction = async ({ request }) => {
  return new Response("Assistant V2: Create new thread", { status: 200 });
};
