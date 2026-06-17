<template>
  <div class="card h-100">
    <img 
      :src="book.cover_url || 'https://via.placeholder.com/300x400?text=No+Cover'" 
      class="card-img-top" 
      alt="book cover"
    >
    <div class="card-body d-flex flex-column">
      <h5 class="card-title">{{ book.title }}</h5>
      <p class="card-text">{{ book.author }}</p>
      
      <div class="mb-3" v-if="book.availability">
        <span class="badge" :class="badgeClass">
          {{ badgeText }}
        </span>
      </div>

      <div class="mt-auto">
        <router-link :to="`/books/${book.isbn13}`" class="btn btn-primary w-100">
          상세보기
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

// 가용성 뱃지 스타일 계산
const badgeClass = computed(() => {
  const status = props.book.availability?.status
  if (status === 'available') return 'text-bg-success text-white'
  if (status === 'loaned') return 'text-bg-warning text-dark'
  if (status === 'none') return 'text-bg-secondary text-white'
  return 'd-none'
})

const badgeText = computed(() => {
  const status = props.book.availability?.status
  if (status === 'available') return '대출가능'
  if (status === 'loaned') return '대출중'
  if (status === 'none') return '미소장'
  return ''
})

const badgeIcon = computed(() => {
  const status = props.book.availability?.status
  if (status === 'available') return 'bi bi-check-circle-fill'
  if (status === 'loaned') return 'bi bi-clock-fill'
  if (status === 'none') return 'bi bi-x-circle-fill'
  return ''
})
</script>
