<template>
  <div class="container d-flex justify-content-center align-items-center" style="min-height: 70vh;">
    <div class="card shadow-lg border-0 rounded-4" style="max-width: 400px; width: 100%;">
      <div class="card-body p-5">
        <h2 class="text-center mb-4 fw-bold text-primary logo-gradient">로그인</h2>
        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label for="username" class="form-label text-secondary">아이디</label>
            <input 
              type="text" 
              class="form-control form-control-lg bg-light border-0" 
              id="username" 
              v-model.trim="username" 
              required
              placeholder="아이디를 입력하세요"
            >
          </div>
          <div class="mb-4">
            <label for="password" class="form-label text-secondary">비밀번호</label>
            <input 
              type="password" 
              class="form-control form-control-lg bg-light border-0" 
              id="password" 
              v-model.trim="password" 
              required
              placeholder="비밀번호를 입력하세요"
            >
          </div>
          
          <div v-if="errorMessage" class="alert alert-danger py-2 mb-4">
            {{ errorMessage }}
          </div>

          <button type="submit" class="btn btn-primary w-100 py-2 fs-5 rounded-pill shadow-sm" :disabled="isLoading">
            <span v-if="isLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isLoading ? '로그인 중...' : '로그인' }}
          </button>
        </form>

        <div class="text-center mt-4 pt-3 border-top">
          <p class="text-muted mb-0">아직 계정이 없으신가요?</p>
          <router-link :to="{ name: 'signup' }" class="text-decoration-none fw-bold">회원가입하기</router-link>
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
const errorMessage = ref('')
const isLoading = ref(false)

const handleLogin = async () => {
  errorMessage.value = ''
  isLoading.value = true
  try {
    await store.logIn({
      username: username.value,
      password: password.value
    })
  } catch (error) {
    if (error.response?.data?.non_field_errors) {
      errorMessage.value = '아이디 또는 비밀번호가 올바르지 않습니다.'
    } else {
      errorMessage.value = '로그인 중 문제가 발생했습니다.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.form-control:focus {
  box-shadow: none;
  border: 1px solid #0d6efd !important;
}
</style>
