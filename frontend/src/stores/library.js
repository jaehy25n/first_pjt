import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/api/axios'
import { useAccountStore } from './accounts'

export const useLibraryStore = defineStore('library', () => {
  const likedList = ref([])
  const readingList = ref([])
  const finishedList = ref([])
  const isLoading = ref(false)
  const isLoaded = ref(false)

  const fetchLibrary = async () => {
    const accountStore = useAccountStore()
    if (!accountStore.isLogin) return

    isLoading.value = true
    try {
      const res = await axiosInstance.get('/api/library')
      likedList.value = res.data.liked || []
      readingList.value = res.data.reading || []
      finishedList.value = res.data.finished || []
      isLoaded.value = true
    } catch (e) {
      console.error('서재 정보 로드 실패:', e)
    } finally {
      isLoading.value = false
    }
  }

  const toggleLike = async (isbn13, bookObj = null) => {
    try {
      const res = await axiosInstance.post('/api/library/toggle-wish', { isbn13 })
      const isLiked = res.data.liked

      if (isLiked) {
        if (!likedList.value.some(b => b.isbn13 === isbn13)) {
          if (bookObj) likedList.value.unshift(bookObj)
        }
      } else {
        likedList.value = likedList.value.filter(b => b.isbn13 !== isbn13)
      }
      return isLiked
    } catch (e) {
      console.error('좋아요 토글 실패:', e)
      return null
    }
  }

  const checkIsLiked = (isbn13) => {
    return likedList.value.some(b => b.isbn13 === isbn13)
  }

  const updateLog = async (isbn13, status) => {
    try {
      await axiosInstance.post('/api/library/log', { isbn13, status })
      await fetchLibrary() // Update local lists
      return true
    } catch (e) {
      console.error('기록 업데이트 실패:', e)
      return false
    }
  }

  return { likedList, readingList, finishedList, isLoading, isLoaded, fetchLibrary, toggleLike, checkIsLiked, updateLog }
})
