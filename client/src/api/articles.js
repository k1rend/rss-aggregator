import http from './http';

/**
 * GET /api/articles
 * @param {{ feedId?: number|null, type?: string|null, limit?: number, offset?: number, order?: 'asc'|'desc', onlyUnviewed?: boolean }} params
 * @returns {Promise<{ total: number, limit: number, offset: number, articles: Array<object> }>}
 */
export async function fetchArticles({
  feedId = null,
  type = null,
  limit = 20,
  offset = 0,
  order = 'desc',
  onlyUnviewed = false,
} = {}) {
  const params = { limit, offset, order };
  if (feedId) params.feed_id = feedId;
  if (type) params.type = type;
  if (onlyUnviewed) params.only_unviewed = true;

  const { data } = await http.get('/api/articles', { params });
  return {
    total: Number(data?.total) || 0,
    limit: Number(data?.limit) || limit,
    offset: Number(data?.offset) || offset,
    articles: Array.isArray(data?.articles) ? data.articles : [],
  };
}

/** GET /api/articles/:id -> single article with `viewed` flag */
export async function fetchArticle(id) {
  const { data } = await http.get(`/api/articles/${id}`);
  return data;
}

/** POST /api/articles/:id/view -> records the view in Redis history */
export async function markArticleViewed(id) {
  const { data } = await http.post(`/api/articles/${id}/view`);
  return data;
}
