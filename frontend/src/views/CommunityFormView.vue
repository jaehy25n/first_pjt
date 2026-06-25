<!-- 게시글 작성 / 수정 (URL 3: /community/create, URL 4: /community/:id/edit) -->
<template>
  <div class="community-form">
    <div class="mb-5">
      <router-link to="/community" class="d-inline-flex align-items-center gap-1 text-muted small mb-4" style="text-decoration:none">
        ← 목록으로
      </router-link>
      <h1 class="h3 fw-bold" style="color:var(--ink)">{{ isEdit ? '게시글 수정' : '새 글 작성' }}</h1>
      <p class="text-muted small mt-1 mb-0">책에 대한 이야기를 자유롭게 나눠보세요.</p>
    </div>

    <form @submit.prevent="submit" class="d-flex flex-column gap-4">
      <!-- 제목 -->
      <div>
        <label class="form-label fw-semibold fs-5" style="color:var(--ink)">제목</label>
        <input
          v-model="form.title"
          type="text"
          class="form-control form-control-lg fs-6"
          placeholder="어떤 이야기인가요?"
          maxlength="100"
          required
        />
        <div class="text-end mt-1">
          <small class="text-muted">{{ form.title.length }}/100</small>
        </div>
      </div>

      <!-- 책 연결 (선택) -->
      <div>
        <label class="form-label fw-semibold fs-5" style="color:var(--ink)">
          관련 책 <span class="fw-normal text-muted">(선택)</span>
        </label>
        <div class="d-flex gap-2">
          <input
            v-model="bookSearch"
            type="text"
            class="form-control"
            placeholder="책 제목으로 검색..."
            @input="searchBooks"
          />
          <button type="button" class="btn btn-outline-secondary flex-shrink-0" @click="clearBook" v-if="selectedBook">제거</button>
        </div>
        <!-- 검색 결과 드롭다운 -->
        <div v-if="bookResults.length" class="border rounded mt-1" style="max-height:200px;overflow-y:auto">
          <button
            v-for="book in bookResults" :key="book.isbn13"
            type="button"
            class="w-100 text-start px-3 py-2 border-0 bg-white d-flex align-items-center gap-2"
            style="cursor:pointer;font-size:0.9rem"
            @click="selectBook(book)"
          >
            <img v-if="book.cover_url" :src="book.cover_url" style="width:30px;height:40px;object-fit:cover" />
            <span>{{ book.title }}</span>
            <small class="text-muted ms-auto">{{ book.author }}</small>
          </button>
        </div>
        <!-- 선택된 책 -->
        <div v-if="selectedBook" class="mt-2 d-flex align-items-center gap-2 p-2 rounded" style="background:var(--bg-soft)">
          <img v-if="selectedBook.cover_url" :src="selectedBook.cover_url" style="width:30px;height:40px;object-fit:cover" />
          <span class="small fw-semibold" style="color:var(--ink)">{{ selectedBook.title }}</span>
          <span class="text-muted small">{{ selectedBook.author }}</span>
        </div>
      </div>

      <!-- 내용 -->
      <div>
        <label class="form-label fw-semibold fs-5" style="color:var(--ink)">내용</label>
        <textarea
          v-model="form.content"
          class="form-control"
          rows="12"
          placeholder="책에 대한 감상, 질문, 정보 등 자유롭게 적어주세요."
          required
          style="resize:vertical"
        ></textarea>
      </div>

      <!-- 버튼 -->
      <div class="d-flex gap-2 justify-content-end border-top pt-4">
        <router-link to="/community" class="btn btn-outline-secondary">취소</router-link>
        <button type="submit" class="btn btn-primary px-4" :disabled="submitting">
          <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
          {{ isEdit ? '수정 완료' : '기록 완료' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccountStore } from '@/stores/accounts'
import axiosInstance from '@/api/axios'

const route = useRoute()
const router = useRouter()
const accountStore = useAccountStore()

const isEdit = computed(() => !!route.params.id)
const form = ref({ title: '', content: '' })
const bookSearch = ref('')
const bookResults = ref([])
const selectedBook = ref(null)
const submitting = ref(false)
let searchTimer = null

// 로그인 안 하면 리다이렉트
if (!accountStore.isLogin) router.push('/login')

// 수정 모드 — 기존 데이터 로드
onMounted(async () => {
  if (isEdit.value) {
    try {
      const res = await axiosInstance.get(`/api/community/${route.params.id}/`)
      const data = res.data
      if (!data.is_mine) { router.push('/community'); return }
      form.value.title = data.title
      form.value.content = data.content
      if (data.book_title) {
        selectedBook.value = { title: data.book_title, cover_url: data.book_cover }
        bookSearch.value = data.book_title
      }
    } catch (e) { router.push('/community') }
  }
})

const searchBooks = () => {
  clearTimeout(searchTimer)
  if (!bookSearch.value.trim()) { bookResults.value = []; return }
  searchTimer = setTimeout(async () => {
    try {
      const res = await axiosInstance.get(`/api/books/?q=${encodeURIComponent(bookSearch.value)}&limit=5`)
      bookResults.value = res.data.results || res.data || []
    } catch (e) { bookResults.value = [] }
  }, 300)
}

const selectBook = (book) => {
  selectedBook.value = book
  bookSearch.value = book.title
  bookResults.value = []
}

const clearBook = () => {
  selectedBook.value = null
  bookSearch.value = ''
  bookResults.value = []
}

const submit = async () => {
  if (submitting.value) return
  submitting.value = true
  const payload = {
    title: form.value.title,
    content: form.value.content,
    book_isbn13: selectedBook.value?.isbn13 || '',
  }
  try {
    if (isEdit.value) {
      await axiosInstance.put(`/api/community/${route.params.id}/`, payload)
      router.push(`/community/${route.params.id}`)
    } else {
      const res = await axiosInstance.post('/api/community/', payload)
      router.push(`/community/${res.data.id}`)
    }
  } catch (e) {
    alert('저장에 실패했습니다. 다시 시도해주세요.')
    console.error(e)
  } finally {
    submitting.value = false
  }
}
</script>
