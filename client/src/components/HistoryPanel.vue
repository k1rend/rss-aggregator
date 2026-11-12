<script setup>
import { computed, onMounted, ref } from 'vue';
import ArticleItem from './ArticleItem.vue';
import { fetchHistory } from '../api/history';
import { apiErrorMessage } from '../api/http';
import { formatDate } from '../utils/format';

const emit = defineEmits(['close']);

const items = ref([]);
const loading = ref(false);
const error = ref('');


const history = computed(() =>
  items.value
    .slice()
    .reverse()
    .map((item) => ({
      ...item,
      id: item.id ?? item.articleId,
      viewed: true,
    }))
);

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const data = await fetchHistory();
    items.value = data.items;
  } catch (err) {
    error.value = apiErrorMessage(err, 'Could not load the viewing history');
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="history">
    <header class="history__header">
      <div>
        <h2 class="history__heading">Viewing history</h2>
        <p class="history__subheading">
          {{ loading ? 'Loading…' : `${items.length} article${items.length === 1 ? '' : 's'} read` }}
          · stored in Redis
        </p>
      </div>
      <button type="button" class="btn btn--ghost" @click="emit('close')">Back to feeds</button>
    </header>

    <p v-if="error" class="alert alert--error">{{ error }}</p>

    <div v-if="loading" class="history__skeleton" aria-hidden="true">
      <div v-for="n in 3" :key="n" class="history__skeleton-row"></div>
    </div>

    <div v-else-if="history.length" class="history__list">
      <ArticleItem v-for="item in history" :key="`${item.id}-${item.viewedAt}`" :article="item">
        <template #meta>
          <span class="history__sep" aria-hidden="true">•</span>
          <span>Viewed {{ formatDate(item.viewed_at) }}</span>
        </template>
      </ArticleItem>
    </div>

    <div v-else class="history__empty">
      <p class="history__empty-title">No reading history yet</p>
      <p class="history__empty-text">
        Expand an article in the feed and it will show up here.
      </p>
    </div>
  </section>
</template>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.history__heading {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.history__subheading {
  margin-top: 2px;
  font-size: 0.84rem;
  color: var(--text-muted);
}

.history__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history__sep {
  opacity: 0.6;
}

.history__skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history__skeleton-row {
  height: 64px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: linear-gradient(90deg, #f4f6fb 25%, #eaeef7 37%, #f4f6fb 63%);
  background-size: 400% 100%;
  animation: history-shimmer 1.4s ease infinite;
}

@keyframes history-shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.history__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 44px 20px;
  text-align: center;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
}

.history__empty-title {
  font-weight: 700;
}

.history__empty-text {
  font-size: 0.86rem;
  color: var(--text-muted);
}
</style>
