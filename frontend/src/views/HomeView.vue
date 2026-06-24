<template>
  <div class="container mt-4">
    <!-- 오늘의 추천 (히어로 섹션 - 심플/모던 버전) -->
    <div class="p-5 mb-5 bg-light rounded-3 shadow-sm">
      <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <div>
            <span class="badge bg-dark mb-2">AI 큐레이션</span>
            <h1 class="display-6 fw-bold">오늘의 추천 도서</h1>
          </div>
          <button @click="refreshRecommendations" class="btn btn-outline-secondary" :disabled="recommendStore.isLoading">
            <span v-if="recommendStore.isLoading" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
            새로고침
          </button>
        </div>

        <!-- 로딩 중 -->
        <div v-if="recommendStore.isLoading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status"></div>
          <p class="mt-3 text-muted">AI가 취향을 분석하여 맞춤형 도서를 선별하고 있습니다... (수 초 소요)</p>
        </div>

        <!-- 데이터 없음 -->
        <div v-else-if="recommendStore.empty" class="alert alert-info py-4 border-0 shadow-sm">
          <h5 class="fw-bold">추천 도서를 찾을 수 없습니다</h5>
          <p class="mb-0">{{ recommendStore.hint }}</p>
        </div>

        <!-- 추천 결과 -->
        <div v-else-if="recommendStore.isLoaded && recommendStore.recommendations.length > 0">
          <div v-for="item in recommendStore.recommendations" :key="item.isbn13" class="card mb-4 border-0 shadow-sm overflow-hidden">
            <div class="row g-0">
              <div class="col-md-3 bg-secondary bg-opacity-10 d-flex justify-content-center align-items-center p-3">
                <router-link :to="`/books/${item.isbn13}`">
                  <img :src="item.cover_url || 'https://via.placeholder.com/150x200?text=No+Cover'" class="img-fluid rounded shadow" :alt="item.title" style="max-height: 250px; object-fit: cover;">
                </router-link>
              </div>
              <div class="col-md-9">
                <div class="card-body h-100 d-flex flex-column p-4">
                  <div class="d-flex justify-content-between align-items-start mb-2">
                    <h4 class="card-title fw-bold mb-0">
                      <router-link :to="`/books/${item.isbn13}`" class="text-reset text-decoration-none">{{ item.title }}</router-link>
                    </h4>
                    <span class="badge bg-success" v-if="item.availability?.status === 'available'">대출가능</span>
                    <span class="badge bg-warning text-dark" v-else-if="item.availability?.status === 'loaned'">대출중</span>
                    <span class="badge bg-secondary" v-else>미소장</span>
                  </div>
                  <p class="card-text text-muted mb-4">{{ item.author }}</p>
                  
                  <div class="alert alert-secondary border-0 bg-secondary bg-opacity-10 p-3 mb-4 flex-grow-1">
                    <p class="mb-1 text-dark fw-bold">왜 이 책인가요?</p>
                    <p class="mb-0 text-dark">{{ item.reason }}</p>
                    <p class="mb-0 mt-2 text-primary" v-if="item.order_note"><small><strong>💡 TIP:</strong> {{ item.order_note }}</small></p>
                  </div>

                  <div v-if="item.similar && item.similar.length > 0" class="mt-auto">
                    <p class="mb-2 text-muted small fw-bold">비슷한 책 (Read-alike)</p>
                    <div class="d-flex flex-wrap gap-3">
                      <router-link v-for="sim in item.similar" :key="sim.isbn13" :to="`/books/${sim.isbn13}`" class="d-flex align-items-center bg-light rounded p-2 pe-3 text-reset text-decoration-none">
                        <img :src="sim.cover_url || 'https://via.placeholder.com/40x60?text=No'" class="rounded shadow-sm me-3" style="width: 40px; height: 60px; object-fit: cover;" :alt="sim.title">
                        <div class="small">
                          <div class="text-truncate fw-bold text-dark" style="max-width: 150px;" :title="sim.title">{{ sim.title }}</div>
                          <div class="text-muted text-truncate" style="max-width: 150px;"><small>{{ sim.author }}</small></div>
                        </div>
                      </router-link>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 취향 발견 (반복정제) -->
    <DiscoverSection />

  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import DiscoverSection from '@/components/DiscoverSection.vue'
import { useRecommendStore } from '@/stores/recommend'

const recommendStore = useRecommendStore()

const refreshRecommendations = () => {
  recommendStore.fetchRecommendations(true)
}

onMounted(() => {
  // 추천 로드 (캐시되어 있으면 API 재호출 안 함)
  recommendStore.fetchRecommendations()
})
</script>

<style scoped>
.card {
  transition: transform 0.2s ease-in-out;
}
.card:hover {
  transform: translateY(-5px);
}
</style>
