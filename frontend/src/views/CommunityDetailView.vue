<!-- 게시글 상세 + 댓글 (URL 2: /community/:id) -->
<template>
  <div class="community-detail" v-if="article">
    <!-- 뒤로가기 -->
    <router-link to="/community" class="d-inline-flex align-items-center gap-1 text-muted small mb-4" style="text-decoration:none">
      ← 목록으로
    </router-link>

    <!-- 게시글 헤더 -->
    <div class="article-head border-bottom pb-4 mb-4">
      <!-- 책 태그 -->
      <div v-if="article.book_title" class="mb-2">
        <router-link :to="`/books/${article.book_isbn}`" class="badge text-decoration-none rounded-pill"
          style="background:var(--accent)">📖 {{ article.book_title }}</router-link>
      </div>
      <h1 class="h3 fw-bold mb-3" style="color:var(--ink)">{{ article.title }}</h1>
      <div class="d-flex align-items-center gap-3 flex-wrap">
        <span class="fw-semibold small" style="color:var(--ink)">{{ article.username }}</span>
        <span class="text-muted small">{{ formatDate(article.created_at) }}</span>
        <span v-if="article.updated_at !== article.created_at" class="text-muted small">(수정됨)</span>
        <span class="text-muted small">댓글 {{ article.comment_count }}</span>

        <!-- 본인 글 수정/삭제 -->
        <div v-if="article.is_mine" class="ms-auto d-flex gap-2">
          <router-link :to="`/community/${article.id}/edit`" class="btn btn-outline-secondary btn-sm">수정</router-link>
          <button class="btn btn-outline-danger btn-sm" @click="deleteArticle">삭제</button>
        </div>
      </div>
    </div>

    <!-- 본문 -->
    <div class="article-body mb-5" style="line-height:1.85; white-space:pre-wrap; color:var(--body)">{{ article.content }}</div>

    <!-- 좋아요 버튼 -->
    <div class="text-center mb-5">
      <button
        class="btn btn-lg d-inline-flex align-items-center gap-2 px-5"
        :class="article.is_liked ? 'btn-primary' : 'btn-outline-primary'"
        @click="toggleLike"
      >
        <span>{{ article.is_liked ? '❤️' : '🤍' }}</span>
        <span>{{ article.like_count }} 좋아요</span>
      </button>
    </div>

    <!-- 댓글 섹션 -->
    <div class="comments-section border-top pt-4">
      <h2 class="h6 fw-semibold mb-4" style="color:var(--ink)">댓글 {{ article.comment_count }}개</h2>

      <!-- 댓글 목록 -->
      <div v-for="comment in article.comments" :key="comment.id" class="comment-row d-flex gap-3 mb-3 pb-3 border-bottom">
        <div class="comment-avatar rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
          style="width:2rem;height:2rem;background:var(--bg-soft);border:1px solid var(--line);font-size:0.8rem;font-weight:700;color:var(--accent)">
          {{ comment.username[0].toUpperCase() }}
        </div>
        <div class="flex-grow-1">
          <div class="d-flex align-items-center gap-2 mb-1">
            <span class="fw-semibold small" style="color:var(--ink)">{{ comment.username }}</span>
            <span class="text-muted" style="font-size:0.75rem">{{ formatDate(comment.created_at) }}</span>
            <button v-if="comment.is_mine" class="btn btn-link p-0 ms-auto text-danger" style="font-size:0.75rem" @click="deleteComment(comment.id)">삭제</button>
          </div>
          <p class="mb-0 small" style="color:var(--body);white-space:pre-wrap">{{ comment.content }}</p>
        </div>
      </div>

      <!-- 댓글 작성 -->
      <div v-if="accountStore.isLogin" class="comment-form mt-4 d-flex gap-2">
        <textarea
          v-model="newComment"
          class="form-control"
          rows="2"
          placeholder="댓글을 입력해 주세요..."
          @keydown.enter.ctrl.prevent="submitComment"
          style="resize:none"
        ></textarea>
        <button class="btn btn-primary px-4 flex-shrink-0" @click="submitComment" :disabled="!newComment.trim()">등록</button>
      </div>
      <div v-else class="mt-4 text-center py-3 bg-soft rounded" style="background:var(--bg-soft)">
        <router-link to="/login" class="text-primary fw-semibold">로그인</router-link>하면 댓글을 달 수 있어요.
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccountStore } from '@/stores/accounts'
import axiosInstance from '@/api/axios'

const route = useRoute()
const router = useRouter()
const accountStore = useAccountStore()

const article = ref(null)
const loading = ref(true)
const newComment = ref('')
const bookIsbn = ref(null)

const formatDate = (str) => {
  const d = new Date(str)
  return `${d.getFullYear()}.${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`
}

const fetchArticle = async () => {
  try {
    const res = await axiosInstance.get(`/api/community/${route.params.id}/`)
    article.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const toggleLike = async () => {
  if (!accountStore.isLogin) { router.push('/login'); return }
  try {
    const res = await axiosInstance.post(`/api/community/${article.value.id}/like/`)
    article.value.is_liked = res.data.liked
    article.value.like_count = res.data.like_count
  } catch (e) { console.error(e) }
}

const submitComment = async () => {
  if (!newComment.value.trim()) return
  try {
    const res = await axiosInstance.post(`/api/community/${article.value.id}/comments/`, { content: newComment.value })
    article.value.comments.push(res.data)
    article.value.comment_count += 1
    newComment.value = ''
  } catch (e) { console.error(e) }
}

const deleteComment = async (commentId) => {
  if (!confirm('댓글을 삭제할까요?')) return
  try {
    await axiosInstance.delete(`/api/community/${article.value.id}/comments/${commentId}/`)
    article.value.comments = article.value.comments.filter(c => c.id !== commentId)
    article.value.comment_count -= 1
  } catch (e) { console.error(e) }
}

const deleteArticle = async () => {
  if (!confirm('게시글을 삭제할까요?')) return
  try {
    await axiosInstance.delete(`/api/community/${article.value.id}/`)
    router.push('/community')
  } catch (e) { console.error(e) }
}

onMounted(fetchArticle)
</script>

<style scoped>
.comment-row:last-child { border-bottom: none !important; }
</style>
