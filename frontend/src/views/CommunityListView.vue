<!-- 커뮤니티 게시글 목록 (URL 1: /community) -->
<template>
  <div class="community-list">
    <!-- 헤더 -->
    <div class="page-header border-bottom pb-4 mb-5">
      <div class="d-flex align-items-end justify-content-between">
        <div>
          <p class="text-muted small mb-1 fw-semibold text-uppercase letter-spacing-wide">Community</p>
          <h1 class="h2 fw-bold mb-0" style="color:var(--ink)">책 이야기</h1>
          <p class="text-muted mt-2 mb-0">독서 경험을 나누고, 같이 읽을 책을 찾아보세요.</p>
        </div>
        <router-link v-if="accountStore.isLogin" to="/community/create" class="btn btn-primary">
          ✏️ 글쓰기
        </router-link>
      </div>

      <!-- 탭 필터 -->
      <div class="mt-4 d-flex gap-2">
        <button
          v-for="tab in tabs" :key="tab.value"
          class="btn btn-sm"
          :class="activeTab === tab.value ? 'btn-dark' : 'btn-outline-secondary'"
          @click="activeTab = tab.value"
        >{{ tab.label }}</button>
      </div>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"><span class="visually-hidden">로딩 중...</span></div>
    </div>

    <!-- 게시글 없음 -->
    <div v-else-if="filteredArticles.length === 0" class="text-center py-5 text-muted">
      <div class="mb-3" style="font-size:2.5rem">💬</div>
      <p class="mb-0">아직 글이 없어요. 첫 번째 이야기를 시작해보세요!</p>
    </div>

    <!-- 게시글 목록 -->
    <div v-else class="article-list">
      <article
        v-for="article in filteredArticles" :key="article.id"
        class="article-row border-bottom py-4 d-flex gap-4 align-items-start"
        @click="$router.push(`/community/${article.id}`)"
        style="cursor:pointer"
      >
        <!-- 좋아요 수 -->
        <div class="text-center" style="min-width:2.5rem">
          <div class="fw-bold" style="color:var(--accent); font-size:1.1rem">{{ article.like_count }}</div>
          <div class="text-muted" style="font-size:0.7rem">좋아요</div>
        </div>

        <!-- 본문 -->
        <div class="flex-grow-1 overflow-hidden">
          <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
            <!-- 책 태그 -->
            <span v-if="article.book_title" class="badge rounded-pill" style="background:var(--accent);font-size:0.7rem">
              📖 {{ article.book_title }}
            </span>
          </div>
          <h2 class="h6 fw-semibold mb-1 text-truncate" style="color:var(--ink)">{{ article.title }}</h2>
          <div class="d-flex align-items-center gap-3">
            <small class="text-muted">{{ article.username }}</small>
            <small class="text-muted">{{ formatDate(article.created_at) }}</small>
            <small class="text-muted">💬 {{ article.comment_count }}</small>
          </div>
        </div>
      </article>
    </div>

    <!-- 내 게시글 보기 (로그인 시) -->
    <div v-if="accountStore.isLogin" class="mt-5 pt-4 border-top text-center">
      <router-link to="/community/me" class="btn btn-outline-secondary btn-sm">내가 쓴 글 보기</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAccountStore } from '@/stores/accounts'
import axiosInstance from '@/api/axios'

const accountStore = useAccountStore()
const articles = ref([])
const loading = ref(true)
const activeTab = ref('all')

const tabs = [
  { value: 'all', label: '전체' },
  { value: 'liked', label: '좋아요 많은 순' },
  { value: 'comments', label: '댓글 많은 순' },
]

const filteredArticles = computed(() => {
  const list = [...articles.value]
  if (activeTab.value === 'liked') return list.sort((a, b) => b.like_count - a.like_count)
  if (activeTab.value === 'comments') return list.sort((a, b) => b.comment_count - a.comment_count)
  return list
})

const formatDate = (str) => {
  const d = new Date(str)
  return `${d.getFullYear()}.${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`
}

onMounted(async () => {
  try {
    const res = await axiosInstance.get('/api/community/')
    articles.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.article-row:hover { background: var(--bg-soft); transition: background 0.15s; }
.letter-spacing-wide { letter-spacing: 0.08em; }
</style>
