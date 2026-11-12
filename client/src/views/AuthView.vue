<script setup>
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { auth } from '../stores/auth';

const route = useRoute();
const router = useRouter();

const mode = ref('signin'); // signin | signup
const login = ref('');
const password = ref('');
const confirmPassword = ref('');
const localError = ref('');

const isSignUp = computed(() => mode.value === 'signup');
const canSubmit = computed(
  () =>
    !auth.state.pending &&
    login.value.trim().length > 0 &&
    password.value.length > 0 &&
    (!isSignUp.value || confirmPassword.value.length > 0)
);

function switchMode(next) {
  if (mode.value === next) return;
  mode.value = next;
  localError.value = '';
  auth.state.error = '';
  confirmPassword.value = '';
}

async function submit() {
  if (!canSubmit.value) return;
  localError.value = '';

  if (isSignUp.value && password.value !== confirmPassword.value) {
    localError.value = 'Passwords do not match';
    return;
  }

  const name = login.value.trim();
  const ok = isSignUp.value
    ? await auth.signUp(name, password.value)
    : await auth.signIn(name, password.value);
  if (!ok) return;

  password.value = '';
  confirmPassword.value = '';
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
  router.replace(redirect.startsWith('/') && !redirect.startsWith('/auth') ? redirect : '/');
}
</script>

<template>
  <div class="auth">
    <div class="auth__card">
      <header class="auth__header">
        <span class="auth__logo" aria-hidden="true">◎</span>
        <h1 class="auth__title">RSS Aggregator</h1>
        <p class="auth__subtitle">
          {{ isSignUp ? 'Create an account to start reading.' : 'Sign in to read your feeds.' }}
        </p>
      </header>

      <div class="auth__tabs" role="tablist">
        <button
          type="button"
          role="tab"
          class="auth__tab"
          :class="{ 'auth__tab--active': mode === 'signin' }"
          :aria-selected="mode === 'signin'"
          @click="switchMode('signin')"
        >
          Log in
        </button>
        <button
          type="button"
          role="tab"
          class="auth__tab"
          :class="{ 'auth__tab--active': mode === 'signup' }"
          :aria-selected="mode === 'signup'"
          @click="switchMode('signup')"
        >
          Sign up
        </button>
      </div>

      <form class="auth__form" novalidate @submit.prevent="submit">
        <label class="field">
          <span class="field__label">Login</span>
          <input
            v-model="login"
            class="field__input"
            type="text"
            name="login"
            autocomplete="username"
            placeholder="alice"
            required
          />
        </label>

        <label class="field">
          <span class="field__label">Password</span>
          <input
            v-model="password"
            class="field__input"
            type="password"
            name="password"
            :autocomplete="isSignUp ? 'new-password' : 'current-password'"
            placeholder="••••••"
            required
          />
        </label>

        <label v-if="isSignUp" class="field">
          <span class="field__label">Repeat password</span>
          <input
            v-model="confirmPassword"
            class="field__input"
            type="password"
            name="confirm-password"
            autocomplete="new-password"
            placeholder="••••••"
          />
        </label>

        <p v-if="isSignUp" class="field__hint">
          Login: 3–32 characters (letters, digits, <code>_</code>, <code>.</code>,
          <code>-</code>). Password: at least 6 characters.
        </p>

        <p v-if="localError || auth.state.error" class="alert alert--error">
          {{ localError || auth.state.error }}
        </p>

        <button type="submit" class="btn btn--primary auth__submit" :disabled="!canSubmit">
          {{ auth.state.pending ? 'Please wait…' : isSignUp ? 'Create account' : 'Log in' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 18px;
  background: radial-gradient(circle at 15% 20%, #dfe8ff 0%, transparent 45%),
    radial-gradient(circle at 85% 85%, #e3f7ec 0%, transparent 45%), var(--bg);
}

.auth__card {
  width: 100%;
  max-width: 400px;
  padding: 30px 28px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}

.auth__header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.auth__logo {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 1.5rem;
  margin-bottom: 4px;
}

.auth__title {
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.auth__subtitle {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.auth__tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin: 22px 0 18px;
  padding: 4px;
  background: var(--surface-alt);
  border-radius: var(--radius-sm);
}

.auth__tab {
  padding: 9px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.auth__tab:hover {
  color: var(--text);
}

.auth__tab--active {
  background: var(--surface);
  color: var(--accent);
  box-shadow: 0 1px 3px rgba(21, 33, 61, 0.12);
}

.auth__tab:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
}

.auth__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.auth__submit {
  margin-top: 4px;
  padding: 11px 16px;
}

code {
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
  font-size: 0.9em;
  background: var(--surface-alt);
  padding: 0 4px;
  border-radius: 4px;
}
</style>
