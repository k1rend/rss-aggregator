import axios from 'axios';

export const TOKEN_STORAGE_KEY = 'rss-aggregator.token';
export const USER_STORAGE_KEY = 'rss-aggregator.user';

// Empty base URL -> requests stay on the current origin and are proxied by Vite
// to the Express server (in vite.config.js).
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { Accept: 'application/json' },
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let unauthorizedHandler = null;

export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof unauthorizedHandler === 'function') {
      unauthorizedHandler();
    }
    return Promise.reject(error);
  }
);

export function apiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  return error?.response?.data?.error || error?.message || fallback;
}

export default http;
