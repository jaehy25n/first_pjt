<!-- 내 게시글 목록 (URL 5: /community/me) -->
<template>
  <div class="my-articles">
    <div class="page-header border-bottom pb-4 mb-5">
      <router-link to="/community" class="d-inline-flex align-items-center gap-1 text-muted small mb-3" style="text-decoration:none">
        ← 목록으로
      </router-link>
      <div class="d-flex align-items-end justify-content-between">
        <div>
          <h1 class="h3 fw-bold mb-1" style="color:var(--ink)">내 기록</h1>
          <p class="text-muted small mb-0">독서 이야기를 잇다</p>
        </div>
      </div>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <!-- 게시글 없음 -->
    <div v-else-if="articles.length === 0" class="text-center py-5 text-muted">
      <div class="mb-3" style="font-size:2.5rem">...</div>
      <p class="mb-3">아직 작성한 글이 없어요.</p>
      <router-link to="/community/create" class="btn btn-outline-primary btn-sm">첫 글 써보기</router-link>
    </div>

    <!-- 통계 카드 -->
    <div v-else>
      <div class="row g-3 mb-5">
        <div class="col-4">
          <div class="p-4 rounded border text-center">
            <div class="h4 fw-bold mb-0" style="color:var(--accent)">{{ articles.length }}</div>
            <small class="text-muted">작성한 글</small>
          </div>
        </div>
        <div class="col-4">
          <div class="p-4 rounded border text-center">
            <div class="h4 fw-bold mb-0" style="color:var(--accent)">{{ totalLikes }}</div>
            <small class="text-muted">받은 좋아요</small>
          </div>
        </div>
        <div class="col-4">
          <div class="p-4 rounded border text-center">
            <div class="h4 fw-bold mb-0" style="color:var(--accent)">{{ totalComments }}</div>
            <small class="text-muted">받은 댓글</small>
          </div>
        </div>
      </div>

      <!-- 게시글 리스트 -->
      <div class="article-list">
        <article
          v-for="article in articles" :key="article.id"
          class="d-flex gap-4 align-items-start border-bottom py-4"
          style="cursor:pointer"
          @click="$router.push(`/community/${article.id}`)"
        >
          <div class="flex-grow-1">
            <span v-if="article.book_title" class="badge rounded-pill mb-1" style="background:var(--accent);font-size:0.7rem">
              {{ article.book_title }}
            </span>
            <h2 class="h6 fw-semibold mb-1" style="color:var(--ink)">{{ article.title }}</h2>
            <div class="d-flex gap-3">
              <small class="text-muted">{{ formatDate(article.created_at) }}</small>
              <small class="text-muted">❤️ {{ article.like_count }}</small>
              <small class="text-muted">댓글 {{ article.comment_count }}</small>
            </div>
          </div>
          <div class="d-flex gap-2 flex-shrink-0">
            <router-link :to="`/community/${article.id}/edit`" class="btn btn-outline-secondary btn-sm" @click.stop>수정</router-link>
            <button class="btn btn-outline-danger btn-sm" @click.stop="deleteArticle(article.id)">삭제</button>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAccountStore } from '@/stores/accounts'
import axiosInstance from '@/api/axios'

const router = useRouter()
const accountStore = useAccountStore()
if (!accountStore.isLogin) router.push('/login')

const articles = ref([])
const loading = ref(true)

const totalLikes = computed(() => articles.value.reduce((s, a) => s + a.like_count, 0))
const totalComments = computed(() => articles.value.reduce((s, a) => s + a.comment_count, 0))

const formatDate = (str) => {
  const d = new Date(str)
  return `${d.getFullYear()}.${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`
}

const deleteArticle = async (id) => {
  if (!confirm('게시글을 삭제할까요?')) return
  try {
    await axiosInstance.delete(`/api/community/${id}/`)
    articles.value = articles.value.filter(a => a.id !== id)
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  try {
    const res = await axiosInstance.get('/api/community/me/')
    articles.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})
</script>
