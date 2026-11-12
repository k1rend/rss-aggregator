import http from './http';

/** GET /api/feeds -> [{ id, url, title, type, article_count }] */
export async function fetchFeeds() {
  const { data } = await http.get('/api/feeds');
  return Array.isArray(data) ? data : [];
}
