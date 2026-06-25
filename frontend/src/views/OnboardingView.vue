<template>
  <div class="container py-4" style="max-width: 920px;">
    <h3 class="fw-bold mb-1">내 독서 취향은?</h3>
    <p class="text-muted mb-4">
      끌리는 책의 표지를 눌러 <span class="text-primary fw-semibold">좋아요</span>를 표시해주세요.
      <span class="text-secondary">읽었든 안 읽었든 괜찮아요 — 취향만 보는 거예요.</span>
    </p>

    <div v-if="loading" class="text-center my-5 text-muted">
      <div class="spinner-border text-secondary" role="status"></div>
      <p class="mt-2">책을 불러오는 중…</p>
    </div>

    <div v-else-if="books.length === 0" class="text-center my-5 text-muted">
      <p>표시할 책이 없어요.</p>
      <button class="btn btn-outline-secondary btn-sm" @click="reshuffle">다시 시도</button>
    </div>

    <div v-else>
      <div class="row g-3">
        <div v-for="book in books" :key="book.isbn13" class="col-6 col-md-3">
          <div
            class="card h-100 shadow-sm pick-card"
            :class="cardClass(book.isbn13)"
            @click="toggle(book.isbn13, 'like')"
          >
            <div class="position-relative">
              <img
                :src="book.cover_url"
                class="card-img-top cover"
                :alt="book.title"
                @error="onImgError"
              />
              <span v-if="picks[book.isbn13] === 'like'" class="badge bg-primary position-absolute top-0 end-0 m-2">
                ❤️ 좋아요
              </span>
            </div>
            <div class="card-body p-2 d-flex flex-column">
              <span v-if="kdcLabel(book.kdc_code)" class="badge bg-light text-dark align-self-start mb-1">{{ kdcLabel(book.kdc_code) }}</span>
              <p class="small fw-semibold mb-0 flex-grow-1 title-clamp">{{ book.title }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="d-flex justify-content-between align-items-center mt-3">
        <button class="btn btn-link text-decoration-none" @click="reshuffle">{{ likedCount > 0 ? '🔄 비슷한 책 더 보기' : '🔄 다른 책 보기' }}</button>
      </div>

      <div class="d-grid mt-4">
        <button
          type="button"
          class="btn btn-success btn-lg"
          :disabled="submitting || likedCount === 0"
          @click="submit"
        >
          {{ submitting ? '저장 중…' : '시작하기' }}
        </button>
        <small v-if="likedCount === 0" class="text-muted text-center mt-2">
          한 권 이상 골라주세요.
        </small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axiosInstance from '@/api/axios'

const router = useRouter()

const KDC_LABELS = {
  '0': '총류', '1': '철학', '2': '종교', '3': '사회과학', '4': '자연과학',
  '5': '기술과학', '6': '예술', '7': '언어', '8': '문학', '9': '역사',
}
const kdcLabel = (code) => KDC_LABELS[(code || '').trim()[0]] || ''

const books = ref([])
const picks = ref({}) // isbn13 -> 'like'
const seen = ref(new Set()) // 이미 보여준 isbn (반복정제 중복 방지)
const goal = ref('')
const loading = ref(true)
const submitting = ref(false)

const likedCount = computed(
  () => Object.values(picks.value).filter((v) => v === 'like').length
)

// 반복정제 발견(D35): 좋아요한 책(picks)을 seed로 비슷한 책을, 없으면 인기순 흩뿌리기.
const fetchBooks = async () => {
  loading.value = true
  try {
    const liked = Object.keys(picks.value).filter((i) => picks.value[i] === 'like')
    const res = await axiosInstance.post('/api/discover', {
      picks: liked,
      seen: [...seen.value],
    })
    const next = (res.data.books || []).slice(0, 12) // 온보딩은 4×3 = 12개 노출
    next.forEach((b) => seen.value.add(b.isbn13))
    books.value = next
  } catch (e) {
    console.error('책 불러오기 실패:', e)
    books.value = []
  } finally {
    loading.value = false
  }
}

const toggle = (isbn, sentiment) => {
  if (picks.value[isbn] === sentiment) {
    delete picks.value[isbn] // 같은 버튼 다시 누르면 해제
  } else {
    picks.value[isbn] = sentiment
  }
}

const cardClass = (isbn) => {
  if (picks.value[isbn] === 'like') return 'border-primary border-2'
  return ''
}

const reshuffle = () => {
  fetchBooks()
}

const onImgError = (e) => {
  e.target.style.visibility = 'hidden'
}

const submit = async () => {
  submitting.value = true
  const liked = Object.keys(picks.value).filter((i) => picks.value[i] === 'like')
  const topics = goal.value.trim() ? [goal.value.trim()] : []
  try {
    await axiosInstance.post('/api/onboarding/taste', { liked, topics })
    router.push({ name: 'home' })
  } catch (e) {
    console.error('취향 저장 실패:', e)
    alert('저장에 실패했어요. 로그인 상태를 확인해주세요.')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchBooks()
})
</script>

<style scoped>
.pick-card {
  cursor: pointer;
  transition: transform 0.15s ease-in-out;
}
.pick-card:hover {
  transform: translateY(-4px);
}
.cover {
  height: 200px;
  object-fit: cover;
}
.title-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
