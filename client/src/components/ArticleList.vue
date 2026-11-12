<script setup>
import ArticleItem from './ArticleItem.vue';

defineProps({
  heading: { type: String, default: 'Articles' },
  subheading: { type: String, default: '' },
  articles: { type: Array, required: true },
  total: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  loadingMore: { type: Boolean, default: false },
  error: { type: String, default: '' },
  canLoadMore: { type: Boolean, default: false },
});

const emit = defineEmits(['view', 'load-more', 'retry']);
</script>

<template>
  <section class="feed-view">
    <header class="feed-view__header">
      <div class="feed-view__titles">
        <h2 class="feed-view__heading">{{ heading }}</h2>
        <p v-if="subheading" class="feed-view__subheading">{{ subheading }}</p>
      </div>

      <div class="legend" aria-hidden="true">
        <span class="legend__item">
          <span class="legend__dot legend__dot--unread"></span>
          Unread
        </span>
        <span class="legend__item">
          <span class="legend__dot legend__dot--read"></span>
          Read
        </span>
      </div>
    </header>

    <p v-if="error" class="alert alert--error">
      {{ error }}
      <button type="button" class="alert__retry" @click="emit('retry')">Retry</button>
    </p>

    <div v-if="loading" class="skeleton-list" aria-hidden="true">
      <div v-for="n in 5" :key="n" class="skeleton"></div>
    </div>

    <template v-else-if="articles.length">
      <div class="article-list">
        <ArticleItem
          v-for="article in articles"
          :key="article.id"
          :article="article"
          @view="emit('view', $event)"
        />
      </div>

      <div class="feed-view__footer">
        <button
          v-if="canLoadMore"
          type="button"
          class="btn"
          :disabled="loadingMore"
          @click="emit('load-more')"
        >
          {{ loadingMore ? 'Loading…' : 'Load more articles' }}
        </button>
        <p v-else class="feed-view__end">End of the feed</p>
      </div>
    </template>

    <div v-else class="empty">
      <p class="empty__title">Nothing here yet</p>
      <p class="empty__text">
        Pick another feed type or feed in the side panel — new articles appear after the
        server refreshes its sources.
      </p>
      <button type="button" class="btn" @click="emit('retry')">Reload articles</button>
    </div>
  </section>
</template>

<style scoped>
.feed-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feed-view__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 4px;
}

.feed-view__titles {
  min-width: 0;
}

.feed-view__heading {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  overflow-wrap: anywhere;
}

.feed-view__subheading {
  font-size: 0.84rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.legend {
  display: flex;
  gap: 14px;
  font-size: 0.76rem;
  color: var(--text-muted);
}

.legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend__dot--unread {
  background: var(--dot-unread);
}

.legend__dot--read {
  background: var(--dot-read);
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feed-view__footer {
  display: flex;
  justify-content: center;
  padding: 6px 0 10px;
}

.feed-view__end {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.alert--error {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.alert__retry {
  border: none;
  background: transparent;
  color: var(--danger);
  font-weight: 700;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
}

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton {
  height: 64px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: linear-gradient(90deg, #f4f6fb 25%, #eaeef7 37%, #f4f6fb 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

@keyframes shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 20px;
  text-align: center;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
}

.empty__title {
  font-weight: 700;
}

.empty__text {
  max-width: 420px;
  font-size: 0.86rem;
  color: var(--text-muted);
}

.empty .btn {
  margin-top: 8px;
}
</style>
