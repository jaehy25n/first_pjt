<template>
  <div class="container mt-5">
    <div class="card mx-auto" style="max-width: 400px;">
      <div class="card-body">
        <h2 class="text-center mb-4">회원가입</h2>
        <form @submit.prevent="handleSignup" class="text-start">
          <div class="mb-3">
            <label for="username" class="form-label">아이디</label>
            <input 
              type="text" 
              class="form-control" 
              id="username" 
              v-model.trim="username" 
              required
            >
          </div>
          <div class="mb-3">
            <label for="password" class="form-label">비밀번호</label>
            <input
              type="password"
              class="form-control"
              id="password"
              v-model.trim="password"
              required
            >
            
          </div>
          <div class="mb-3">
            <label for="passwordConfirm" class="form-label">비밀번호 확인</label>
            <input 
              type="password" 
              class="form-control" 
              id="passwordConfirm" 
              v-model.trim="passwordConfirm" 
              required
            >
          </div>
          <div class="mb-4">
            <label for="email" class="form-label">이메일 (선택)</label>
            <input 
              type="email" 
              class="form-control" 
              id="email" 
              v-model.trim="email" 
            >
          </div>
          
          <div v-if="errorMessage" class="alert alert-danger py-2 mb-4">
            {{ errorMessage }}
          </div>

          <button type="submit" class="btn btn-primary w-100 py-2" :disabled="isLoading">
            <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isLoading ? '가입 중...' : '회원가입' }}
          </button>
        </form>

        <div class="text-center mt-4 pt-3 border-top">
          <p class="text-muted mb-0">이미 계정이 있으신가요?</p>
          <router-link :to="{ name: 'login' }" class="text-decoration-none">로그인하기</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAccountStore } from '@/stores/accounts'

const store = useAccountStore()

const username = ref('')
const password = ref('')
const passwordConfirm = ref('')
const email = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const handleSignup = async () => {
  if (password.value !== passwordConfirm.value) {
    errorMessage.value = '비밀번호가 일치하지 않습니다.'
    return
  }

  errorMessage.value = ''
  isLoading.value = true
  try {
    await store.signUp({
      username: username.value,
      password1: password.value,
      password2: passwordConfirm.value,
      email: email.value
    })
  } catch (error) {
    if (error.response?.data) {
      const errors = error.response.data
      let msg = ''
      for (const key in errors) {
        msg += `${errors[key][0]}\n`
      }
      errorMessage.value = msg || '회원가입 중 문제가 발생했습니다.'
    } else {
      errorMessage.value = '회원가입 중 문제가 발생했습니다.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>
