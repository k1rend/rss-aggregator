import http from './http';

/** POST /api/auth/signup -> { token, user } */
export async function signUp({ login, password }) {
  const { data } = await http.post('/api/auth/signup', { login, password });
  return data;
}

/** POST /api/auth/signin -> { token, user } */
export async function signIn({ login, password }) {
  const { data } = await http.post('/api/auth/signin', { login, password });
  return data;
}
