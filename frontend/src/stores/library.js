import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/api/axios'
import { useAccountStore } from './accounts'

export const useLibraryStore = defineStore('library', () => {
  const wishList = ref([])
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
      wishList.value = res.data.wish || []
      readingList.value = res.data.reading || []
      finishedList.value = res.data.finished || []
      isLoaded.value = true
    } catch (e) {
      console.error('서재 정보 로드 실패:', e)
    } finally {
      isLoading.value = false
    }
  }

  const toggleWish = async (isbn13, bookObj = null) => {
    try {
      const res = await axiosInstance.post('/api/library/toggle-wish', { isbn13 })
      const isWished = res.data.wished
      
      if (isWished) {
        if (!wishList.value.some(b => b.isbn13 === isbn13)) {
          if (bookObj) wishList.value.unshift(bookObj)
        }
      } else {
        wishList.value = wishList.value.filter(b => b.isbn13 !== isbn13)
      }
      return isWished
    } catch (e) {
      console.error('찜 토글 실패:', e)
      return null
    }
  }
  
  const checkIsWished = (isbn13) => {
    return wishList.value.some(b => b.isbn13 === isbn13)
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

  return { wishList, readingList, finishedList, isLoading, isLoaded, fetchLibrary, toggleWish, checkIsWished, updateLog }
})
