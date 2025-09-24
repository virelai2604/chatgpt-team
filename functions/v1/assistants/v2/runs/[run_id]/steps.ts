import type { PagesFunction } from '../../../../../[[path]]';
export const onRequest: PagesFunction = async ({ request }) => {
  return new Response("Assistant V2: GET steps for run {run_id}", { status: 200 });
};
