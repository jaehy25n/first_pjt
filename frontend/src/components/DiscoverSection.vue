<template>
  <div class="mb-5">
    <div class="d-flex justify-content-between align-items-center mb-1">
      <h2 class="fw-bold mb-0">이런 책도 잇다</h2>
    </div>
    <p class="text-muted mb-3">
      마음에 드는 책을 더 많이 고를수록,<span class="text-primary fw-semibold"> 내 취향에 딱 맞는 책들이 나타납니다.</span>
    </p>

    <!-- 도서관 미선택 등 빈 상태 -->
    <div v-if="empty" class="alert alert-info border-0 shadow-sm d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span>{{ hint }}</span>
      <router-link to="/onboarding" class="btn btn-outline-primary btn-sm">도서관 고르기</router-link>
    </div>

    <!-- 에러: 다시 시도 -->
    <div v-else-if="error" class="alert alert-danger border-0 shadow-sm d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span>책을 불러오는 중 문제가 생겼어요.</span>
      <button class="btn btn-outline-danger btn-sm" @click="fetchSpread">다시 시도</button>
    </div>

    <template v-else>
      <div v-if="books.length" class="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-5 g-2">
        <div v-for="book in books" :key="book.isbn13" class="col">
          <div
            class="card h-100 shadow-sm discover-card"
            :class="isPicked(book.isbn13) ? 'border-primary border-2' : ''"
            @click="togglePick(book.isbn13)"
          >
            <div class="position-relative">
              <img
                :src="book.cover_url || 'https://via.placeholder.com/150x200?text=No+Cover'"
                class="card-img-top cover" :alt="book.title" @error="onImgError"
              />
              <span class="badge position-absolute top-0 end-0 m-2" :class="badgeClass(book)">{{ badgeText(book) }}</span>
              <span v-if="isPicked(book.isbn13)" class="badge bg-primary position-absolute top-0 start-0 m-2">
                <i class="bi bi-check-lg"></i> 선택
              </span>
            </div>
            <div class="card-body p-2 d-flex flex-column">
              <p class="small fw-semibold mb-1 title-clamp">{{ book.title }}</p>
              <p class="text-muted mb-2" style="font-size: 0.75rem;">{{ book.author }}</p>
              <router-link
                :to="`/books/${book.isbn13}`" class="btn btn-outline-secondary btn-sm mt-auto"
                @click.stop
              >상세보기</router-link>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="text-center my-5 text-muted">
        <p>더 보여드릴 책이 없어요.</p>
        <button class="btn btn-outline-primary btn-sm" @click="reset">처음부터 다시</button>
      </div>

      <div v-if="loading" class="text-center my-4 text-muted">
        <div class="spinner-border spinner-border-sm" role="status"></div> 불러오는 중…
      </div>

      <div v-if="books.length" class="d-flex justify-content-center mt-3 gap-3">
        <button v-if="picks.length || seen.length" class="btn btn-outline-secondary btn-sm px-5 fs-6" @click="reset">
        처음부터
        </button>
        <button class="btn btn-primary px-4 fs-6" :disabled="loading" @click="fetchSpread">
          {{ picks.length ? '고른 취향으로 더 보기' : '다른 책 보기' }}
          <i class="bi bi-arrow-repeat ms-1"></i>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axiosInstance from '@/api/axios'

const books = ref([])
const picks = ref([])   // 누적 선택 isbn
const seen = ref([])    // 누적으로 보여준 isbn
const loading = ref(false)
const empty = ref(false)
const error = ref(false)
const hint = ref('')

const isPicked = (isbn) => picks.value.includes(isbn)

const togglePick = (isbn) => {
  const i = picks.value.indexOf(isbn)
  if (i === -1) picks.value.push(isbn)
  else picks.value.splice(i, 1)
}

const fetchSpread = async () => {
  loading.value = true
  error.value = false
  try {
    const res = await axiosInstance.post('/api/discover', { picks: picks.value, seen: seen.value })
    if (res.data.empty) {
      empty.value = true
      hint.value = res.data.hint
      books.value = []
      return
    }
    const next = res.data.books || []
    seen.value = [...seen.value, ...next.map(b => b.isbn13)]
    books.value = next
  } catch (e) {
    console.error('발견 로드 실패:', e)
    error.value = true
    books.value = []
  } finally {
    loading.value = false
  }
}

const reset = () => {
  picks.value = []
  seen.value = []
  empty.value = false
  fetchSpread()
}

const onImgError = (e) => { e.target.style.visibility = 'hidden' }

const badgeClass = (book) => {
  const s = book.availability?.status
  if (s === 'available') return 'bg-success'
  if (s === 'loaned') return 'bg-warning text-dark'
  return 'd-none'
}
const badgeText = (book) => {
  const s = book.availability?.status
  if (s === 'available') return '대출가능'
  if (s === 'loaned') return '대출중'
  return ''
}

onMounted(fetchSpread)
</script>

<style scoped>
.discover-card { cursor: pointer; transition: transform 0.15s ease-in-out; }
.discover-card:hover { transform: translateY(-4px); }
.cover { height: 210px; object-fit: cover; }
.title-clamp {
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
</style>
