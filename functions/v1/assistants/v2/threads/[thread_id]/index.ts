import type { PagesFunction } from '../../../../../[[path]]';
export const onRequest: PagesFunction = async ({ request }) => {
  return new Response("Assistant V2: POST to thread {thread_id}", { status: 200 });
};
