<template>
  <div class="card h-100">
    <div class="position-relative">
      <img 
        :src="book.cover_url || 'https://via.placeholder.com/300x400?text=No+Cover'" 
        class="card-img-top object-fit-cover" 
        style="height: 250px;"
        alt="book cover"
      >
      <button 
        v-if="accountStore.isLogin"
        @click.prevent="handleWishToggle"
        class="btn btn-light position-absolute top-0 end-0 m-2 rounded-circle shadow-sm p-2 d-flex align-items-center justify-content-center"
        style="width: 40px; height: 40px; z-index: 10;"
      >
        <i :class="isWished ? 'bi bi-heart-fill text-danger' : 'bi bi-heart text-secondary'" style="font-size: 1.2rem;"></i>
      </button>
    </div>
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
import { useLibraryStore } from '@/stores/library'
import { useAccountStore } from '@/stores/accounts'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const libraryStore = useLibraryStore()
const accountStore = useAccountStore()

const isWished = computed(() => {
  return libraryStore.checkIsWished(props.book.isbn13)
})

const handleWishToggle = async () => {
  await libraryStore.toggleWish(props.book.isbn13, props.book)
}

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
