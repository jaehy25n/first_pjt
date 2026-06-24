import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/api/axios'
import { useAccountStore } from './accounts'

export const useRecommendStore = defineStore('recommend', () => {
  const recommendations = ref([])
  const isLoading = ref(false)
  const isLoaded = ref(false)
  const empty = ref(false)
  const error = ref(false)
  const hint = ref('')

  const fetchRecommendations = async (force = false) => {
    // 비로그인은 호출하지 않음(홈에서 로그인 CTA로 안내)
    const accountStore = useAccountStore()
    if (!accountStore.isLogin) return

    // 이미 불러왔고 강제 새로고침이 아니면 캐시 유지
    if (isLoaded.value && !force) return

    isLoading.value = true
    empty.value = false
    error.value = false
    hint.value = ''
    recommendations.value = []

    try {
      const response = await axiosInstance.post('/api/recommendations', { limit: 5 })
      if (response.data.empty) {
        empty.value = true
        hint.value = response.data.hint || '관심사를 넓히거나 도서관을 추가해 보세요'
      } else {
        recommendations.value = response.data.items || []
      }
      isLoaded.value = true
    } catch (e) {
      // 실패는 '빈 상태'가 아니라 '에러' — 화면에서 다시 시도 안내
      console.error('추천 도서를 불러오는데 실패했습니다:', e)
      error.value = true
    } finally {
      isLoading.value = false
    }
  }

  return {
    recommendations,
    isLoading,
    isLoaded,
    empty,
    error,
    hint,
    fetchRecommendations,
  }
})
