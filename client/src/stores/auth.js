import { reactive } from 'vue';
import {
  apiErrorMessage,
  onUnauthorized,
  TOKEN_STORAGE_KEY,
  USER_STORAGE_KEY,
} from '../api/http';
import { signIn as apiSignIn, signUp as apiSignUp } from '../api/auth';

function readStoredUser() {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

// Session state lives in a module-level reactive object so every component sees
// the same token/user without pulling in an extra state library.
const state = reactive({
  token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
  user: readStoredUser(),
  pending: false,
  error: '',
});

function setSession({ token, user }) {
  state.token = token;
  state.user = user;
  state.error = '';
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

function clearSession() {
  state.token = '';
  state.user = null;
  state.pending = false;
  state.error = '';
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

async function authenticate(request, login, password) {
  state.pending = true;
  state.error = '';
  try {
    const session = await request({ login, password });
    setSession(session);
    return true;
  } catch (error) {
    state.error = apiErrorMessage(error, 'Authentication failed');
    return false;
  } finally {
    state.pending = false;
  }
}

export const auth = {
  state,
  signIn: (login, password) => authenticate(apiSignIn, login, password),
  signUp: (login, password) => authenticate(apiSignUp, login, password),
  logout: clearSession,
};

// An expired token makes the API answer 401 -> drop the session, App.vue then
// sends the user back to the auth screen.
onUnauthorized(clearSession);
