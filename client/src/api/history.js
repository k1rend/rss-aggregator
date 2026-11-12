import http from './http';

/**
 * GET /api/history
 * @param {{ from?: number, to?: number, details?: boolean }} params
 * @returns {Promise<{ count: number, items: Array<object> }>}
 */
export async function fetchHistory({ from = 0, to = -1, details = true } = {}) {
  const { data } = await http.get('/api/history', { params: { from, to, details } });
  return {
    count: Number(data?.count) || 0,
    items: Array.isArray(data?.items) ? data.items : [],
  };
}
