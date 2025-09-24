import type { PagesFunction } from '../[[path]]';  // Adjusted import path to match your codebase

export const onRequest: PagesFunction = async ({ request }) => {
  const url = new URL(request.url);
  const method = request.method.toUpperCase();

  if (method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405 });
  }

  // Extract the job ID from the URL path: /v1/fine_tuning/jobs/{job_id}/cancel
  const segments = url.pathname.split('/');
  const jobId = segments[4]; // 0: "", 1: "v1", 2: "fine_tuning", 3: "jobs", 4: "{job_id}"

  if (!jobId) {
    return new Response('Missing job_id in path', { status: 400 });
  }

  const upstreamUrl = `https://api.openai.com/v1/fine_tuning/jobs/${jobId}/cancel`;

  const resp = await fetch(upstreamUrl, {
    method,
    headers: request.headers
  });

  return new Response(resp.body, {
    status: resp.status,
    headers: resp.headers
  });
};