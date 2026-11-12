<script setup>
import { computed } from 'vue';

const props = defineProps({
  feeds: { type: Array, required: true },
  selectedType: { type: String, default: 'all' },
  selectedFeedId: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  user: { type: Object, default: null },
  historyOpen: { type: Boolean, default: false },
});

const emit = defineEmits([
  'select-type',
  'select-feed',
  'toggle-history',
  'refresh-feeds',
  'logout',
]);

const TYPES = [
  { value: 'all', label: 'All feeds' },
  { value: 'local', label: 'Tech' },
  { value: 'country', label: 'Economy' },
  { value: 'world', label: 'World' },
];

const visibleFeeds = computed(() =>
  props.selectedType === 'all'
    ? props.feeds
    : props.feeds.filter((feed) => feed.type === props.selectedType)
);
</script>

<template>
  <aside class="sidebar">
    <header class="sidebar__brand">
      <span class="sidebar__logo" aria-hidden="true">◎</span>
      <div class="sidebar__brand-text">
        <h1 class="sidebar__title">RSS Aggregator</h1>
        <p class="sidebar__user">
          Signed in as <strong>{{ user?.login || 'unknown' }}</strong>
        </p>
      </div>
    </header>

    <section class="sidebar__section">
      <h2 class="sidebar__heading">Feed type</h2>
      <div class="type-list">
        <button
          v-for="type in TYPES"
          :key="type.value"
          type="button"
          class="type-btn"
          :class="{ 'type-btn--active': selectedType === type.value }"
          @click="emit('select-type', type.value)"
        >
          {{ type.label }}
        </button>
      </div>
    </section>

    <section class="sidebar__section sidebar__section--grow">
      <h2 class="sidebar__heading">
        <span>RSS feeds</span>
        <button
          type="button"
          class="sidebar__refresh"
          title="Reload feeds"
          aria-label="Reload feeds"
          :disabled="loading"
          @click="emit('refresh-feeds')"
        >
          ⟳
        </button>
      </h2>

      <p v-if="error" class="sidebar__note sidebar__note--error">{{ error }}</p>
      <p v-else-if="loading" class="sidebar__note">Loading feeds…</p>
      <p v-else-if="!visibleFeeds.length" class="sidebar__note">No feeds for this type yet.</p>

      <ul v-else class="feed-list">
        <li v-for="feed in visibleFeeds" :key="feed.id">
          <button
            type="button"
            class="feed-btn"
            :class="{ 'feed-btn--active': selectedFeedId === feed.id }"
            :title="feed.url"
            @click="emit('select-feed', feed)"
          >
            <span class="feed-btn__title">{{ feed.title }}</span>
            <span class="feed-btn__count">{{ feed.article_count }}</span>
          </button>
        </li>
      </ul>
    </section>

    <footer class="sidebar__footer">
      <button
        type="button"
        class="btn btn--block"
        :class="{ 'btn--primary': historyOpen }"
        @click="emit('toggle-history')"
      >
        <span aria-hidden="true">🕘</span>
        {{ historyOpen ? 'Back to feeds' : 'View history' }}
      </button>
      <button type="button" class="btn btn--ghost btn--block" @click="emit('logout')">
        Log out
      </button>
    </footer>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 300px;
  flex: 0 0 300px;
  padding: 22px 18px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  height: 100vh;
  position: sticky;
  top: 0;
  overflow: hidden;
}

.sidebar__brand {
  display: flex;
  gap: 12px;
  align-items: center;
}

.sidebar__logo {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 1.3rem;
  flex: 0 0 auto;
}

.sidebar__brand-text {
  min-width: 0;
}

.sidebar__title {
  font-size: 1.02rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.sidebar__user {
  font-size: 0.78rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar__section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
}

.sidebar__section--grow {
  flex: 1 1 auto;
  overflow: hidden;
}

.sidebar__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  font-weight: 700;
}

.sidebar__refresh {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.95rem;
  line-height: 1;
  padding: 2px 5px;
  border-radius: 6px;
  color: var(--text-muted);
}

.sidebar__refresh:hover:not(:disabled) {
  background: var(--surface-alt);
  color: var(--accent);
}

.sidebar__refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.type-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.type-btn {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.type-btn:hover {
  /* background: var(--surface-alt); */
  background: var(--accent-hover);

}

.type-btn--active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.type-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.sidebar__note {
  font-size: 0.82rem;
  color: var(--text-muted);
}

.sidebar__note--error {
  color: var(--danger);
}

.feed-list {
  list-style: none;
  margin: 0;
  padding: 0 4px 0 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
  min-height: 0;
}

.feed-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  text-align: left;
  font-size: 0.88rem;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.feed-btn:hover {
  background: var(--surface-alt);
}

.feed-btn--active {
  background: var(--accent-soft);
  border-color: #c9d6ff;
  color: #1e3ecb;
  font-weight: 600;
}

.feed-btn__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.feed-btn__count {
  flex: 0 0 auto;
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  color: var(--text-muted);
  background: var(--surface-alt);
  border-radius: 999px;
  padding: 1px 7px;
}

.feed-btn--active .feed-btn__count {
  background: #fff;
  color: #1e3ecb;
}

.sidebar__footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px solid var(--border);
  padding-top: 16px;
}

@media (max-width: 900px) {
  .sidebar {
    width: 100%;
    flex: 0 0 auto;
    height: auto;
    position: static;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }

  .sidebar__section--grow {
    max-height: 220px;
  }
}
</style>
