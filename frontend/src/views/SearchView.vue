<template>
  <div class="container mt-4">
    <div class="mb-4">
      <h1 class="text-start">어떤 책을 찾으시나요?</h1>
      <p class="mb-5 text-start">도서 제목이나 저자를 검색하시면, 주 도서관의 대출 가능 여부까지 한 번에 알려드립니다.</p>
      
      <form @submit.prevent="handleSearch" class="d-flex gap-2">
        <input 
          type="text" 
          class="form-control" 
          v-model.trim="searchQuery" 
          placeholder="책 제목 또는 저자 입력"
        >
        <button class="btn btn-primary text-nowrap" type="submit" :disabled="isSearching">
          <span v-if="isSearching" class="spinner-border spinner-border-sm" aria-hidden="true"></span>
          <span v-else>검색</span>
        </button>
      </form>
    </div>

    <!-- 로딩 스피너 -->
    <div v-if="isSearching" class="text-center my-5">
      <div class="spinner-border" role="status"></div>
      <p>검색 중입니다...</p>
    </div>

    <!-- 에러 메시지 -->
    <div v-else-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
    </div>

    <!-- 검색 결과 영역 -->
    <div v-else-if="hasSearched">
      <div class="mb-3">
        <h5>검색 결과 {{ totalCount }}건</h5>
      </div>

      <!-- 도서 카드 그리드 -->
      <div v-if="books.length > 0">
        <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4 mb-4">
          <div class="col" v-for="book in books" :key="book.isbn13">
            <BookCard :book="book" />
          </div>
        </div>

        <!-- 페이징 (다음/이전) -->
        <div class="d-flex justify-content-center gap-2 mb-5">
          <button 
            @click="loadPage(currentPage - 1)" 
            class="btn btn-outline-primary" 
            :disabled="!prevPageUrl"
          >
            이전
          </button>
          <span class="align-self-center">{{ currentPage }} 페이지</span>
          <button 
            @click="loadPage(currentPage + 1)" 
            class="btn btn-outline-primary" 
            :disabled="!nextPageUrl"
          >
            다음
          </button>
        </div>
      </div>

      <!-- 결과 없음 -->
      <div v-else class="text-center my-5">
        <h5>검색 결과가 없습니다.</h5>
        <p>다른 검색어로 다시 시도해 보세요.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axiosInstance from '@/api/axios'
import BookCard from '@/components/BookCard.vue'

const searchQuery = ref('')
const hasSearched = ref(false)
const isSearching = ref(false)
const errorMessage = ref('')

const books = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const nextPageUrl = ref(null)
const prevPageUrl = ref(null)

const handleSearch = () => {
  if (!searchQuery.value) return
  fetchBooks(1)
}

const loadPage = (page) => {
  fetchBooks(page)
}

const fetchBooks = async (page) => {
  isSearching.value = true
  errorMessage.value = ''
  
  try {
    const res = await axiosInstance.get(`/api/books/?q=${encodeURIComponent(searchQuery.value)}&page=${page}`)
    books.value = res.data.results || []
    totalCount.value = res.data.count || 0
    nextPageUrl.value = res.data.next
    prevPageUrl.value = res.data.previous
    currentPage.value = page
    hasSearched.value = true
  } catch (error) {
    console.error('검색 실패:', error)
    errorMessage.value = '검색 중 오류가 발생했습니다.'
  } finally {
    isSearching.value = false
  }
}
</script>
