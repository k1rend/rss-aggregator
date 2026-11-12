<script setup>
import { computed, onBeforeUnmount, ref } from 'vue';
import DOMPurify from 'dompurify';
import { formatDate } from '../utils/format';
import { copyToClipboard } from '../utils/share';

const props = defineProps({
  article: { type: Object, required: true },
});

const emit = defineEmits(['view']);

const expanded = ref(false);
const shareState = ref('idle'); // idle | copied | error
const shareError = ref('');
let shareResetTimer = null;

const isRead = computed(() => Boolean(props.article.viewed));

// Feed content is arbitrary HTML from third-party RSS sources, so it is
// sanitized before being rendered with v-html.
const safeContent = computed(() =>
  DOMPurify.sanitize(props.article.content || '', { USE_PROFILES: { html: true } })
);

const hasContent = computed(
  () => safeContent.value.replace(/<[^>]*>/g, '').trim().length > 0
);

function toggle() {
  expanded.value = !expanded.value;
  // Expanding an unread article marks it as read. The parent owns the API call
  // so it can update the shared list state optimistically.
  if (expanded.value && !isRead.value) {
    emit('view', props.article);
  }
}

async function share() {
  shareState.value = 'idle';
  shareError.value = '';
  try {
    await copyToClipboard(props.article.link);
    shareState.value = 'copied';
  } catch (error) {
    shareState.value = 'error';
    shareError.value = error?.message || 'Could not copy the link';
  }
  if (shareResetTimer) clearTimeout(shareResetTimer);
  shareResetTimer = setTimeout(() => {
    if (shareState.value !== 'idle') shareState.value = 'idle';
  }, 2600);
}

onBeforeUnmount(() => {
  if (shareResetTimer) clearTimeout(shareResetTimer);
});
</script>

<template>
  <article class="article" :class="{ 'article--read': isRead, 'article--expanded': expanded }">
    <button type="button" class="article__row" :aria-expanded="expanded" @click="toggle">
      <span
        class="article__dot"
        :class="isRead ? 'article__dot--read' : 'article__dot--unread'"
        role="img"
        :aria-label="isRead ? 'Read' : 'Unread'"
        :title="isRead ? 'Read' : 'Unread'"
      ></span>

      <span class="article__main">
        <span class="article__title">{{ article.title }}</span>
        <span class="article__meta">
          <span class="article__feed">{{ article.feed_title }}</span>
          <span class="article__sep" aria-hidden="true">•</span>
          <span>{{ formatDate(article.pub_date) }}</span>
          <slot name="meta"></slot>
        </span>
      </span>

      <span
        class="article__arrow"
        :class="{ 'article__arrow--open': expanded }"
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 24 24"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          stroke-width="2.2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M9 6l6 6-6 6" />
        </svg>
      </span>
    </button>

    <div v-if="expanded" class="article__body">
      <div v-if="hasContent" class="article__content" v-html="safeContent"></div>
      <p v-else class="article__placeholder">
        No content was stored for this article. Open the source link to read it in full.
      </p>

      <div class="article__actions">
        <button type="button" class="btn article__share" @click="share">
          <svg
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M10 13a5 5 0 0 0 7.07 0l2-2a5 5 0 0 0-7.07-7.07l-1 1" />
            <path d="M14 11a5 5 0 0 0-7.07 0l-2 2A5 5 0 0 0 12 20.07l1-1" />
          </svg>
          {{ shareState === 'copied' ? 'Link copied' : 'Share' }}
        </button>

        <a
          class="article__source"
          :href="article.link"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open source
        </a>

        <span v-if="shareState === 'copied'" class="article__hint">
          Source link copied to clipboard
        </span>
        <span v-else-if="shareState === 'error'" class="article__hint article__hint--error">
          {{ shareError }}
        </span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.article {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.article:hover {
  border-color: #c9d4e8;
}

.article--expanded {
  border-color: #c9d6ff;
  box-shadow: 0 10px 26px rgba(21, 33, 61, 0.07);
}

.article__row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 14px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.article__row:hover {
  background: var(--surface-alt);
}

.article__row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.article__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex: 0 0 auto;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.article__dot--unread {
  background: var(--dot-unread);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.18);
}

.article__dot--read {
  background: var(--dot-read);
  box-shadow: none;
}

.article__main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.article__title {
  font-size: 0.97rem;
  font-weight: 600;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.article--read .article__title {
  color: #414c62;
  font-weight: 500;
}

.article__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 0.76rem;
  color: var(--text-muted);
}

.article__feed {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article__sep {
  opacity: 0.6;
}

.article__arrow {
  display: grid;
  place-items: center;
  color: var(--text-muted);
  transition: transform 0.2s ease, color 0.15s ease;
}

.article__row:hover .article__arrow {
  color: var(--accent);
}

.article__arrow--open {
  transform: rotate(90deg);
  color: var(--accent);
}

.article__body {
  padding: 0 16px 16px 40px;
  border-top: 1px solid var(--border);
  background: #fcfdff;
}

.article__content {
  padding-top: 14px;
  font-size: 0.92rem;
  line-height: 1.65;
  color: #2a3448;
  overflow-wrap: anywhere;
}

.article__content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-sm);
}

.article__content :deep(a) {
  word-break: break-word;
}

.article__content :deep(p) {
  margin: 0 0 0.8em;
}

.article__content :deep(iframe),
.article__content :deep(script),
.article__content :deep(style) {
  display: none;
}

.article__placeholder {
  padding-top: 14px;
  font-size: 0.9rem;
  color: var(--text-muted);
  font-style: italic;
}

.article__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed var(--border);
}

.article__share {
  padding: 7px 14px;
  font-weight: 600;
}

.article__source {
  font-size: 0.84rem;
  font-weight: 600;
  text-decoration: none;
}

.article__source:hover {
  text-decoration: underline;
}

.article__hint {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.article__hint--error {
  color: var(--danger);
}

@media (max-width: 640px) {
  .article__body {
    padding-left: 16px;
  }
}
</style>
