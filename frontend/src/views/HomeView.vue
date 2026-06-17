<template>
  <div class="container mt-4">
    <!-- 오늘의 추천 (히어로 섹션 - 심플/모던 버전) -->
    <div class="p-5 mb-4 bg-light rounded-3">
      <div class="container-fluid py-5">
        <span class="badge bg-dark mb-3">AI 큐레이션</span>
        <h1 class="display-5 fw-bold">오늘의 추천 도서</h1>
        <p class="col-md-8 fs-4">
          사용자의 독서 취향과 현재 도서관의 대출 가능 여부를 분석하여, 
          바로 빌려볼 수 있는 가장 완벽한 책을 제안합니다.
        </p>
        <button class="btn btn-primary btn-lg disabled" type="button">추천받기 (준비중)</button>
      </div>
    </div>

    <!-- 탐색하기 (도서 목록) -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>탐색하기</h2>
      <router-link to="/search" class="btn btn-outline-primary">
        전체보기
      </router-link>
    </div>

    <!-- 로딩 스피너 -->
    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border" role="status"></div>
      <p>도서 목록을 불러오는 중입니다...</p>
    </div>

    <!-- 에러 메시지 -->
    <div v-else-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
    </div>

    <!-- 도서 카드 그리드 -->
    <div v-else class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4 mb-5">
      <div class="col" v-for="book in books" :key="book.isbn13">
        <BookCard :book="book" />
      </div>
    </div>

    <!-- 결과 없음 -->
    <div v-if="!isLoading && !errorMessage && books.length === 0" class="text-center my-5">
      <p>등록된 도서가 없습니다.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axiosInstance from '@/api/axios'
import BookCard from '@/components/BookCard.vue'

const books = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

onMounted(async () => {
  try {
    const res = await axiosInstance.get('/api/books/')
    // API returns { count, next, previous, results: [...] }
    books.value = res.data.results || []
  } catch (error) {
    console.error('도서 목록 로드 실패:', error)
    errorMessage.value = '도서 목록을 불러오는 중 오류가 발생했습니다.'
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
/* 심플한 모던 디자인에서는 불필요한 배경 장식 제거 */
</style>
