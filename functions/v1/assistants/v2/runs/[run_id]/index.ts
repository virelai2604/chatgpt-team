import type { PagesFunction } from '../../../../../[[path]]';
export const onRequest: PagesFunction = async ({ request }) => {
  return new Response("Assistant V2: GET run {run_id}", { status: 200 });
};
