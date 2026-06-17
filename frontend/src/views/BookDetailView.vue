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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axiosInstance from '@/api/axios'

const route = useRoute()
const isbn13 = route.params.isbn13

const book = ref(null)
const availabilities = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

onMounted(async () => {
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
