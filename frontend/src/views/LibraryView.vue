<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="fw-bold mb-0">내 서재</h2>
      <button class="btn btn-outline-secondary btn-sm" @click="libraryStore.fetchLibrary">
        새로고침
      </button>
    </div>

    <!-- 로딩 스피너 -->
    <div v-if="libraryStore.isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-3">서재 정보를 불러오는 중입니다...</p>
    </div>

    <div v-else>
      <!-- 탭 네비게이션 -->
      <ul class="nav nav-tabs mb-4" id="libraryTabs" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active fw-bold text-danger" id="liked-tab" data-bs-toggle="tab" data-bs-target="#liked" type="button" role="tab" aria-controls="liked" aria-selected="true">
            <i class="bi bi-heart-fill me-1"></i> 좋아요 ({{ libraryStore.likedList.length }})
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link fw-bold text-primary" id="reading-tab" data-bs-toggle="tab" data-bs-target="#reading" type="button" role="tab" aria-controls="reading" aria-selected="false">
            <i class="bi bi-book me-1"></i> 읽는 중 ({{ libraryStore.readingList.length }})
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link fw-bold text-success" id="finished-tab" data-bs-toggle="tab" data-bs-target="#finished" type="button" role="tab" aria-controls="finished" aria-selected="false">
            <i class="bi bi-check-circle-fill me-1"></i> 완독 ({{ libraryStore.finishedList.length }})
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link fw-bold text-info" id="stats-tab" data-bs-toggle="tab" data-bs-target="#stats" type="button" role="tab" aria-controls="stats" aria-selected="false">
            <i class="bi bi-bar-chart-fill me-1"></i> 독서 통계
          </button>
        </li>
      </ul>

      <!-- 탭 콘텐츠 -->
      <div class="tab-content" id="libraryTabsContent">
        
        <!-- 좋아요 -->
        <div class="tab-pane fade show active" id="liked" role="tabpanel" aria-labelledby="liked-tab">
          <div v-if="libraryStore.likedList.length === 0" class="text-center my-5 text-muted">
            <i class="bi bi-heart fs-1 mb-3 d-block"></i>
            <p>아직 좋아요한 책이 없습니다.</p>
            <router-link to="/search" class="btn btn-outline-primary mt-2">책 탐색하기</router-link>
          </div>
          <div v-else class="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-5 g-3">
            <div class="col" v-for="book in libraryStore.likedList" :key="book.isbn13">
              <BookCard :book="book" />
            </div>
          </div>
        </div>

        <!-- 읽는 중 -->
        <div class="tab-pane fade" id="reading" role="tabpanel" aria-labelledby="reading-tab">
          <div v-if="libraryStore.readingList.length === 0" class="text-center my-5 text-muted">
            <i class="bi bi-book fs-1 mb-3 d-block"></i>
            <p>현재 읽고 있는 책이 없습니다.</p>
          </div>
          <div v-else class="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-5 g-3">
            <div class="col" v-for="book in libraryStore.readingList" :key="book.isbn13">
              <BookCard :book="book" />
            </div>
          </div>
        </div>

        <!-- 완독 -->
        <div class="tab-pane fade" id="finished" role="tabpanel" aria-labelledby="finished-tab">
          <div v-if="libraryStore.finishedList.length === 0" class="text-center my-5 text-muted">
            <i class="bi bi-check-circle fs-1 mb-3 d-block"></i>
            <p>아직 완독한 책이 없습니다.</p>
          </div>
          <div v-else class="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-5 g-3">
            <div class="col" v-for="book in libraryStore.finishedList" :key="book.isbn13">
              <!-- 완독 탭의 경우 별점이 있으면 카드에 작게 표시해주는 것도 좋지만, 기본 BookCard 활용 -->
              <div class="position-relative h-100">
                <BookCard :book="book" />
                <div v-if="book.rating" class="position-absolute top-0 start-0 m-2 badge bg-warning text-dark border shadow-sm z-index-10">
                  <i class="bi bi-star-fill text-danger me-1"></i> {{ book.rating }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 독서 통계 -->
        <div class="tab-pane fade" id="stats" role="tabpanel" aria-labelledby="stats-tab">
          <div v-if="libraryStore.finishedList.length === 0" class="text-center my-5 text-muted">
            <i class="bi bi-bar-chart fs-1 mb-3 d-block"></i>
            <p>아직 통계를 낼 완독 데이터가 없습니다.</p>
          </div>
          <div v-else class="row g-4">
            <div class="col-md-6">
              <div class="card shadow-sm h-100">
                <div class="card-body">
                  <h5 class="card-title fw-bold mb-4">월별 완독 권수</h5>
                  <div style="height: 300px;">
                    <Bar :data="chartDataMonthly" :options="chartOptions" />
                  </div>
                </div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="card shadow-sm h-100">
                <div class="card-body">
                  <h5 class="card-title fw-bold mb-4">완독 주제(KDC) 분포</h5>
                  <div style="height: 300px; display: flex; justify-content: center;">
                    <Doughnut :data="chartDataKdc" :options="chartOptions" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useLibraryStore } from '@/stores/library'
import BookCard from '@/components/BookCard.vue'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement)

const libraryStore = useLibraryStore()

const kdcMap = {
  '0': '총류', '1': '철학', '2': '종교', '3': '사회과학', '4': '자연과학',
  '5': '기술과학', '6': '예술', '7': '언어', '8': '문학', '9': '역사'
}

const chartDataMonthly = computed(() => {
  const counts = {}
  libraryStore.finishedList.forEach(book => {
    if (book.finished_at) {
      const month = book.finished_at.substring(0, 7) // 'YYYY-MM'
      counts[month] = (counts[month] || 0) + 1
    }
  })
  
  const labels = Object.keys(counts).sort()
  const data = labels.map(l => counts[l])
  
  return {
    labels: labels.length ? labels : ['이번 달'],
    datasets: [{
      label: '완독 권수',
      backgroundColor: '#0d6efd',
      data: data.length ? data : [0]
    }]
  }
})

const chartDataKdc = computed(() => {
  const counts = {}
  libraryStore.finishedList.forEach(book => {
    const kdcCode = book.kdc_code ? String(book.kdc_code) : ''
    const firstDigit = kdcCode.charAt(0)
    const subject = kdcMap[firstDigit] || '기타'
    counts[subject] = (counts[subject] || 0) + 1
  })
  
  const labels = Object.keys(counts)
  const data = Object.values(counts)
  
  return {
    labels: labels.length ? labels : ['데이터 없음'],
    datasets: [{
      backgroundColor: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0', '#6f42c1', '#fd7e14', '#20c997', '#6c757d', '#e83e8c'],
      data: data.length ? data : [1]
    }]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false
}

onMounted(() => {
  // 컴포넌트 마운트 시 항상 최신 상태를 불러옴
  libraryStore.fetchLibrary()
})
</script>

<style scoped>
.nav-link {
  color: #6c757d;
}
.nav-link.active {
  background-color: transparent;
  border-bottom: 3px solid currentColor;
}
.z-index-10 {
  z-index: 10;
}
</style>
