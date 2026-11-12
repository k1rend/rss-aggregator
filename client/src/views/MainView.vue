<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import Sidebar from '../components/Sidebar.vue';
import ArticleList from '../components/ArticleList.vue';
import HistoryPanel from '../components/HistoryPanel.vue';
import { fetchFeeds } from '../api/feeds';
import { fetchArticles, markArticleViewed } from '../api/articles';
import { apiErrorMessage } from '../api/http';
import { auth } from '../stores/auth';

const PAGE_SIZE = 20;
const TYPE_LABELS = {
  all: 'All feeds',
  local: 'Tech news',
  country: 'Economy news',
  world: 'World news',
};

const router = useRouter();

const feeds = ref([]);
const feedsLoading = ref(false);
const feedsError = ref('');

const selectedType = ref('all');
const selectedFeedId = ref(null);

const articles = ref([]);
const total = ref(0);
const articlesLoading = ref(false);
const articlesLoadingMore = ref(false);
const articlesError = ref('');
const notice = ref('');

const showHistory = ref(false);

const selectedFeed = computed(
  () => feeds.value.find((feed) => feed.id === selectedFeedId.value) || null
);

const heading = computed(
  () => selectedFeed.value?.title || TYPE_LABELS[selectedType.value] || 'Articles'
);

const subheading = computed(() => {
  if (articlesLoading.value) return 'Loading articles…';
  if (!total.value) return 'Nothing to show for this selection';
  const noun = total.value === 1 ? 'article' : 'articles';
  return `${total.value} ${noun} · showing ${articles.value.length}`;
});

const canLoadMore = computed(() => articles.value.length < total.value);

async function loadFeeds() {
  feedsLoading.value = true;
  feedsError.value = '';
  try {
    feeds.value = await fetchFeeds();
    if (selectedFeedId.value && !feeds.value.some((feed) => feed.id === selectedFeedId.value)) {
      selectedFeedId.value = null;
    }
  } catch (error) {
    feedsError.value = apiErrorMessage(error, 'Could not load feeds');
  } finally {
    feedsLoading.value = false;
  }
}

function currentFilters() {
  return {
    feedId: selectedFeedId.value,
    type:
      selectedFeedId.value || selectedType.value === 'all' ? null : selectedType.value,
    limit: PAGE_SIZE,
  };
}

async function loadArticles() {
  articlesLoading.value = true;
  articlesError.value = '';
  notice.value = '';
  try {
    const data = await fetchArticles({ ...currentFilters(), offset: 0 });
    articles.value = data.articles;
    total.value = data.total;
  } catch (error) {
    articlesError.value = apiErrorMessage(error, 'Could not load articles');
    articles.value = [];
    total.value = 0;
  } finally {
    articlesLoading.value = false;
  }
}

async function loadMoreArticles() {
  if (articlesLoadingMore.value || !canLoadMore.value) return;
  articlesLoadingMore.value = true;
  try {
    const data = await fetchArticles({ ...currentFilters(), offset: articles.value.length });
    const knownIds = new Set(articles.value.map((article) => article.id));
    articles.value = [
      ...articles.value,
      ...data.articles.filter((article) => !knownIds.has(article.id)),
    ];
    total.value = data.total;
  } catch (error) {
    notice.value = apiErrorMessage(error, 'Could not load more articles');
  } finally {
    articlesLoadingMore.value = false;
  }
}

// Expanding an article marks it as read and stores the view in Redis history.
async function handleView(article) {
  if (article.viewed) return;
  article.viewed = true; // optimistic update
  try {
    await markArticleViewed(article.id);
  } catch (error) {
    article.viewed = false;
    notice.value = apiErrorMessage(error, 'Could not save the read state');
  }
}

function handleSelectType(type) {
  selectedType.value = type;
  selectedFeedId.value = null;
  showHistory.value = false;
}

function handleSelectFeed(feed) {
  selectedFeedId.value = feed.id;
  selectedType.value = feed.type;
  showHistory.value = false;
}

function toggleHistory() {
  showHistory.value = !showHistory.value;
}

function handleLogout() {
  auth.logout();
  router.replace({ name: 'auth' });
}

watch([selectedType, selectedFeedId], () => {
  loadArticles();
});

onMounted(() => {
  loadFeeds();
  loadArticles();
});
</script>

<template>
  <div class="shell">
    <Sidebar
      :feeds="feeds"
      :selected-type="selectedType"
      :selected-feed-id="selectedFeedId"
      :loading="feedsLoading"
      :error="feedsError"
      :user="auth.state.user"
      :history-open="showHistory"
      @select-type="handleSelectType"
      @select-feed="handleSelectFeed"
      @toggle-history="toggleHistory"
      @refresh-feeds="loadFeeds"
      @logout="handleLogout"
    />

    <main class="content">
      <div class="content__inner">
        <p v-if="notice" class="notice" role="status">
          <span>{{ notice }}</span>
          <button type="button" class="notice__close" aria-label="Dismiss" @click="notice = ''">
            ×
          </button>
        </p>

        <HistoryPanel v-if="showHistory" @close="showHistory = false" />

        <ArticleList
          v-else
          :heading="heading"
          :subheading="subheading"
          :articles="articles"
          :total="total"
          :loading="articlesLoading"
          :loading-more="articlesLoadingMore"
          :error="articlesError"
          :can-load-more="canLoadMore"
          @view="handleView"
          @load-more="loadMoreArticles"
          @retry="loadArticles"
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  align-items: flex-start;
  min-height: 100vh;
  background: var(--bg);
}

.content {
  flex: 1 1 auto;
  min-width: 0;
  height: 100vh;
  overflow-y: auto;
}

.content__inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 28px 30px 56px;
}

.notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  background: #fff6e5;
  border: 1px solid #f3ddb4;
  color: #7a5a12;
  font-size: 0.85rem;
}

.notice__close {
  border: none;
  background: transparent;
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
  color: inherit;
}

@media (max-width: 900px) {
  .shell {
    flex-direction: column;
  }

  .content {
    height: auto;
  }

  .content__inner {
    padding: 22px 16px 40px;
  }
}
</style>
