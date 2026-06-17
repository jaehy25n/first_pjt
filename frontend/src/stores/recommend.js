import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/api/axios'

export const useRecommendStore = defineStore('recommend', () => {
  const recommendations = ref([])
  const isLoading = ref(false)
  const isLoaded = ref(false)
  const empty = ref(false)
  const hint = ref('')

  const fetchRecommendations = async (force = false) => {
    // 이미 불러왔고 강제 새로고침이 아니면 캐시된 데이터 유지
    if (isLoaded.value && !force) {
      return
    }

    isLoading.value = true
    empty.value = false
    hint.value = ''
    recommendations.value = []

    try {
      const response = await axiosInstance.post('/api/recommendations', {
        limit: 5
      })
      
      if (response.data.empty) {
        empty.value = true
        hint.value = response.data.hint
      } else {
        recommendations.value = response.data.items || []
      }
      isLoaded.value = true
    } catch (error) {
      console.error('추천 도서를 불러오는데 실패했습니다:', error)
      empty.value = true
      hint.value = '추천을 불러오는 중 오류가 발생했습니다.'
    } finally {
      isLoading.value = false
    }
  }

  return {
    recommendations,
    isLoading,
    isLoaded,
    empty,
    hint,
    fetchRecommendations
  }
})
