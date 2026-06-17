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
          <button class="nav-link active fw-bold text-danger" id="wish-tab" data-bs-toggle="tab" data-bs-target="#wish" type="button" role="tab" aria-controls="wish" aria-selected="true">
            <i class="bi bi-heart-fill me-1"></i> 찜한 책 ({{ libraryStore.wishList.length }})
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
      </ul>

      <!-- 탭 콘텐츠 -->
      <div class="tab-content" id="libraryTabsContent">
        
        <!-- 찜한 책 -->
        <div class="tab-pane fade show active" id="wish" role="tabpanel" aria-labelledby="wish-tab">
          <div v-if="libraryStore.wishList.length === 0" class="text-center my-5 text-muted">
            <i class="bi bi-heart fs-1 mb-3 d-block"></i>
            <p>아직 찜한 책이 없습니다.</p>
            <router-link to="/search" class="btn btn-outline-primary mt-2">책 탐색하기</router-link>
          </div>
          <div v-else class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">
            <div class="col" v-for="book in libraryStore.wishList" :key="book.isbn13">
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
          <div v-else class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">
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
          <div v-else class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">
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

      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useLibraryStore } from '@/stores/library'
import BookCard from '@/components/BookCard.vue'

const libraryStore = useLibraryStore()

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
