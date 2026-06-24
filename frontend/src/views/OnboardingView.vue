<template>
  <div class="container py-4" style="max-width: 920px;">
    <h3 class="fw-bold mb-1">취향 고르기</h3>
    <p class="text-muted mb-4">
      끌리는 책에 <span class="text-primary fw-semibold">좋아요</span>를 눌러주세요.
      <span class="text-secondary">읽었든 안 읽었든 괜찮아요 — 취향만 보는 거예요.</span>
    </p>

    <div class="mb-4">
      <label class="form-label small fw-semibold mb-2">
        이용할 도서관을 골라주세요 <span class="text-secondary">(선택 · 여러 곳 가능)</span>
        <span class="text-muted">— 고른 도서관의 '지금 대출 가능' 여부가 책에 배지로 표시돼요 (나중에 추가해도 돼요)</span>
      </label>
      <div v-if="selectedLibs.length > 0" class="d-flex flex-wrap gap-2 mb-2">
        <button
          v-for="code in selectedLibs"
          :key="code"
          type="button"
          class="btn btn-sm btn-primary"
          @click="toggleLib({ lib_code: code, name: selectedMeta[code] })"
        >{{ selectedMeta[code] }} ✕</button>
      </div>

      <div class="d-flex flex-wrap gap-2 mb-2">
        <button type="button" class="btn btn-sm btn-outline-primary" :disabled="locating" @click="findNearby">
          📍 {{ locating ? '위치 확인 중…' : '내 근처 도서관 찾기' }}
        </button>
        <input
          v-model="searchQ"
          type="text"
          class="form-control form-control-sm"
          style="max-width: 220px;"
          placeholder="또는 도서관 이름 검색"
          @keyup.enter="searchLibs"
        />
      </div>
      <div v-if="libError" class="text-muted small mb-2">{{ libError }}</div>

      <div v-if="nearbyLibs.length > 0" class="list-group">
        <button
          v-for="lib in nearbyLibs"
          :key="lib.lib_code"
          type="button"
          class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
          :class="{ active: selectedLibs.includes(lib.lib_code) }"
          @click="toggleLib(lib)"
        >
          <span>{{ lib.name }} <small class="text-muted">{{ lib.address }}</small></span>
          <small v-if="lib.distance_km != null" class="text-nowrap">{{ lib.distance_km }}km</small>
        </button>
      </div>
    </div>

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
        <div v-for="book in books" :key="book.isbn13" class="col-6 col-md-4 col-lg-3">
          <div class="card h-100 shadow-sm" :class="cardClass(book.isbn13)">
            <img
              :src="book.cover_url"
              class="card-img-top cover"
              :alt="book.title"
              @error="onImgError"
            />
            <div class="card-body p-2 d-flex flex-column">
              <span v-if="kdcLabel(book.kdc_code)" class="badge bg-light text-dark align-self-start mb-1">{{ kdcLabel(book.kdc_code) }}</span>
              <p class="small fw-semibold mb-2 flex-grow-1 title-clamp">{{ book.title }}</p>
              <button
                type="button"
                class="btn btn-sm w-100"
                :class="picks[book.isbn13] === 'like' ? 'btn-primary' : 'btn-outline-primary'"
                @click="toggle(book.isbn13, 'like')"
              >{{ picks[book.isbn13] === 'like' ? '👍 좋아요 ✓' : '👍 좋아요' }}</button>
            </div>
          </div>
        </div>
      </div>

      <div class="d-flex justify-content-between align-items-center mt-3">
        <button class="btn btn-link text-decoration-none" @click="reshuffle">{{ likedCount > 0 ? '🔄 비슷한 책 더 보기' : '🔄 다른 책 보기' }}</button>
        <small class="text-muted">좋아요 {{ likedCount }}</small>
      </div>

      <div class="mt-4">
        <label class="form-label small fw-semibold">요즘 어떤 책이 읽고 싶나요? <span class="text-muted">(선택)</span></label>
        <input
          v-model="goal"
          type="text"
          class="form-control"
          placeholder="예: 위로받고 싶어요 / 데이터 분석 입문"
        />
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
const selectedLibs = ref([])     // lib_code 배열 (제출용)
const selectedMeta = ref({})     // lib_code -> name (선택 칩 표시용)
const nearbyLibs = ref([])       // 근처/검색 결과
const locating = ref(false)
const libError = ref('')
const searchQ = ref('')

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
    const next = res.data.books || []
    next.forEach((b) => seen.value.add(b.isbn13))
    books.value = next
  } catch (e) {
    console.error('책 불러오기 실패:', e)
    books.value = []
  } finally {
    loading.value = false
  }
}

const toggleLib = (lib) => {
  const code = lib.lib_code
  const i = selectedLibs.value.indexOf(code)
  if (i === -1) {
    selectedLibs.value.push(code)
    selectedMeta.value[code] = lib.name
  } else {
    selectedLibs.value.splice(i, 1)
  }
}

const findNearby = () => {
  libError.value = ''
  if (!navigator.geolocation) {
    libError.value = '이 브라우저는 위치를 지원하지 않아요. 이름으로 검색해 주세요.'
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      try {
        const res = await axiosInstance.get('/api/libraries/nearby/', {
          params: { lat: pos.coords.latitude, lng: pos.coords.longitude, n: 10 },
        })
        nearbyLibs.value = res.data.libraries || []
        if (nearbyLibs.value.length === 0) libError.value = '근처 도서관을 찾지 못했어요.'
      } catch (e) {
        libError.value = '근처 도서관을 불러오지 못했어요.'
      } finally {
        locating.value = false
      }
    },
    () => {
      locating.value = false
      libError.value = '위치 권한이 꺼져 있어요. 이름으로 검색해 주세요.'
    },
    { timeout: 8000 }
  )
}

const searchLibs = async () => {
  const q = searchQ.value.trim()
  if (!q) return
  libError.value = ''
  try {
    const res = await axiosInstance.get('/api/libraries/', { params: { q } })
    nearbyLibs.value = res.data || []
    if (nearbyLibs.value.length === 0) libError.value = '검색 결과가 없어요.'
  } catch (e) {
    libError.value = '검색에 실패했어요.'
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
    // 선택 도서관들 먼저 저장(추천이 이 도서관들 기준) → 취향 저장
    if (selectedLibs.value.length > 0) {
      await axiosInstance.patch('/api/profile/onboarding/', { library_codes: selectedLibs.value })
    }
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
