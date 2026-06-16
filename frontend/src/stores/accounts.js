import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axiosInstance from '@/api/axios'

export const useAccountStore = defineStore('account', () => {
  const token = ref(null)
  const user = ref(null)
  const router = useRouter()

  const isLogin = computed(() => {
    return token.value !== null
  })

  const signUp = async function ({ username, password1, password2, email }) {
    try {
      await axiosInstance.post('/accounts/signup/', {
        username,
        password1,
        password2,
        email
      })
      console.log('회원 가입이 완료되었습니다.')
      // Auto login after sign up
      await logIn({ username, password: password1 })
    } catch (error) {
      console.error('회원 가입 실패:', error)
      throw error
    }
  }

  const logIn = async function ({ username, password }) {
    try {
      const response = await axiosInstance.post('/accounts/login/', {
        username,
        password
      })
      console.log('로그인이 완료되었습니다.')
      token.value = response.data.key
      // Redirect to home page upon successful login
      router.push({ name: 'home' })
    } catch (error) {
      console.error('로그인 실패:', error)
      throw error
    }
  }

  const logOut = async function () {
    try {
      await axiosInstance.post('/accounts/logout/')
      console.log('로그아웃이 완료되었습니다.')
    } catch (error) {
      console.error('로그아웃 실패:', error)
    } finally {
      token.value = null
      user.value = null
      router.push({ name: 'login' })
    }
  }

  return {
    token,
    user,
    isLogin,
    signUp,
    logIn,
    logOut
  }
}, {
  persist: true
})
