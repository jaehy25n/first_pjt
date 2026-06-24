<template>
  <div class="container mt-5">
    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border" role="status"></div>
      <p>도서 정보를 불러오는 중입니다...</p>
    </div>

    <div v-else-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
    </div>

    <div v-else-if="book">
      <div class="row">
        <!-- 1단: 표지 및 기본 정보 (좌측) -->
        <div class="col-md-4 mb-4">
          <div class="card">
            <img 
              :src="book.cover_url || 'https://via.placeholder.com/300x400?text=No+Cover'" 
              class="card-img-top img-fluid" 
              alt="book cover"
            >
            <div class="card-body">
              <p class="mb-1"><strong>저자:</strong> {{ book.author }}</p>
              <p class="mb-1"><strong>출판사:</strong> {{ book.publisher }}</p>
              <p class="mb-1"><strong>출판연도:</strong> {{ book.pub_year }}</p>
              <p class="mb-0"><strong>KDC:</strong> {{ book.kdc_code }}</p>

              <div class="mt-3" v-if="accountStore.isLogin">
                <div class="read-slider" :class="{ 'is-busy': statusUpdating }">
                  <span
                    class="read-slider-thumb"
                    :data-status="currentStatus"
                    :style="{ transform: `translateX(${activeIndex * 100}%)` }"
                  ></span>
                  <button
                    v-for="opt in STATUS_OPTS"
                    :key="opt.value"
                    type="button"
                    class="read-slider-opt"
                    :class="{ active: currentStatus === opt.value }"
                    :disabled="statusUpdating"
                    @click="setStatus(opt.value)"
                  >{{ opt.label }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2단: 도서 소개 및 도서관 가용성 (우측) -->
        <div class="col-md-8">
          <h2 class="mb-3">{{ book.title }}</h2>
          <div class="mb-4">
            <h5>도서 소개</h5>
            <p style="white-space: pre-wrap;">{{ book.description || '도서 소개가 제공되지 않습니다.' }}</p>
          </div>

          <div v-if="keywords.length > 0" class="mb-4">
            <h5 class="mb-2">연관 키워드</h5>
            <span v-for="kw in keywords" :key="kw.word" class="badge rounded-pill text-bg-light me-1 mb-1">
              #{{ kw.word }}
            </span>
          </div>

          <hr class="my-4">

          <div>
            <h5 class="mb-3">도서관별 소장 및 대출 현황</h5>
            
            <div v-if="availabilities.length > 0">
              <div class="list-group">
                <div v-for="avail in availabilities" :key="avail.lib_code" class="list-group-item d-flex justify-content-between align-items-center">
                  <div>
                    <h6 class="mb-0">{{ avail.library_name }}</h6>
                    <small v-if="!avail.has_book" class="text-muted">미소장</small>
                    <small v-else-if="avail.loan_available" class="text-success">대출가능</small>
                    <small v-else class="text-warning">대출중</small>
                  </div>
                  
                  <div>
                    <span v-if="!avail.has_book" class="badge text-bg-secondary">미소장</span>
                    <span v-else-if="avail.loan_available" class="badge text-bg-success">대출가능</span>
                    <span v-else class="badge text-bg-warning">대출중</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="alert alert-secondary">
              등록된 도서관 중 이 책을 소장한 곳이 없습니다.
            </div>
          </div>

          <hr class="my-4">

          <div>
            <h5 class="mb-3">이 책이 있는 서울 도서관</h5>
            <div v-if="seoulLoading" class="text-muted small">서울 도서관 소장 정보를 불러오는 중…</div>
            <div v-else-if="seoulLibraries.length > 0">
              <p class="text-muted small mb-2">서울 전역 {{ seoulLibraries.length }}곳에서 소장 중</p>
              <div class="list-group">
                <div v-for="lib in seoulLibraries" :key="lib.lib_code" class="list-group-item">
                  <h6 class="mb-0">{{ lib.name }}</h6>
                  <small class="text-muted">{{ lib.address }}</small>
                </div>
              </div>
            </div>
            <div v-else class="text-muted small">소장 도서관 정보를 확인할 수 없어요.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axiosInstance from '@/api/axios'
import { useAccountStore } from '@/stores/accounts'
import { useLibraryStore } from '@/stores/library'

const route = useRoute()
const isbn13 = route.params.isbn13

const accountStore = useAccountStore()
const libraryStore = useLibraryStore()

const book = ref(null)
const availabilities = ref([])
const seoulLibraries = ref([])
const seoulLoading = ref(true)
const keywords = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

const statusUpdating = ref(false)

// 읽기 진행 슬라이더 (찜 제외): 'none'(읽기 전) | 'reading' | 'finished'
const STATUS_OPTS = [
  { value: 'none', label: '읽기 전' },
  { value: 'reading', label: '읽는 중' },
  { value: 'finished', label: '완독' },
]
const currentStatus = computed(() => {
  if (libraryStore.finishedList.some(b => b.isbn13 === isbn13)) return 'finished'
  if (libraryStore.readingList.some(b => b.isbn13 === isbn13)) return 'reading'
  return 'none' // 읽기 전 (찜은 이 컨트롤에서 제외 — 카드 하트로)
})
const activeIndex = computed(() => STATUS_OPTS.findIndex(o => o.value === currentStatus.value))

const setStatus = async (value) => {
  if (statusUpdating.value || value === currentStatus.value) return
  statusUpdating.value = true
  try {
    await libraryStore.updateLog(isbn13, value) // 'none'(읽기 전)이면 백엔드가 행 삭제
  } finally {
    statusUpdating.value = false
  }
}

const fetchSeoulLibraries = async () => {
  try {
    const res = await axiosInstance.get(`/api/books/${isbn13}/seoul-libraries/`)
    seoulLibraries.value = res.data.libraries || []
  } catch (e) {
    seoulLibraries.value = []
  } finally {
    seoulLoading.value = false
  }
}

const fetchUsage = async () => {
  try {
    const res = await axiosInstance.get(`/api/books/${isbn13}/usage/`)
    keywords.value = res.data.keywords || []
  } catch (e) {
    keywords.value = []
  }
}

onMounted(async () => {
  if (accountStore.isLogin && !libraryStore.isLoaded) {
    libraryStore.fetchLibrary()
  }
  fetchSeoulLibraries() // 서울 소장관 목록은 비동기로(메인 로드 막지 않게)
  fetchUsage() // 연관 키워드 비동기 로드 (⑧)
  try {
    // 도서 기본 상세 정보 및 가용성 동시 호출
    const [bookRes, availRes] = await Promise.all([
      axiosInstance.get(`/api/books/${isbn13}/`),
      axiosInstance.get(`/api/books/${isbn13}/availability/`)
    ])
    
    book.value = bookRes.data
    availabilities.value = availRes.data
  } catch (error) {
    console.error('도서 상세 로드 실패:', error)
    errorMessage.value = '도서 정보를 불러오는 중 오류가 발생했습니다.'
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.read-slider {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  background-color: #e9ecef;
  border-radius: 999px;
  padding: 4px;
  user-select: none;
}
.read-slider.is-busy { opacity: 0.6; pointer-events: none; }
.read-slider-thumb {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc((100% - 8px) / 3);
  height: calc(100% - 8px);
  border-radius: 999px;
  background-color: #6c757d;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  transition: transform 0.25s ease, background-color 0.25s ease;
}
.read-slider-thumb[data-status="reading"] { background-color: #0d6efd; }
.read-slider-thumb[data-status="finished"] { background-color: #198754; }
.read-slider-opt {
  position: relative;
  z-index: 1;
  border: 0;
  background: transparent;
  padding: 6px 0;
  font-size: 0.9rem;
  color: #6c757d;
  cursor: pointer;
  transition: color 0.25s ease;
}
.read-slider-opt.active { color: #fff; font-weight: 600; }
</style>
