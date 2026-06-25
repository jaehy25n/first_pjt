<template>
  <div id="app-container" class="d-flex flex-column min-vh-100">
    <header>
      <nav class="navbar navbar-expand-md navbar-light bg-white border-bottom fixed-top shadow-sm">
        <div class="container">
          <router-link to="/" class="navbar-brand">책잇다</router-link>
          
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent" aria-controls="navbarContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          
          <div class="collapse navbar-collapse" id="navbarContent">
            <ul class="navbar-nav me-auto mb-2 mb-md-0">
              <li class="nav-item">
                <router-link to="/" class="nav-link" active-class="active">홈</router-link>
              </li>
              <li class="nav-item">
                <router-link to="/search" class="nav-link" active-class="active">검색</router-link>
              </li>
              <li class="nav-item" v-if="store.isLogin">
                <router-link to="/library" class="nav-link" active-class="active">내 서재</router-link>
              </li>
            </ul>
            <div class="d-flex align-items-center mt-2 mt-md-0">
              <template v-if="!store.isLogin">
                <router-link to="/login" class="btn btn-outline-primary me-2">로그인</router-link>
                <router-link to="/signup" class="btn btn-primary">회원가입</router-link>
              </template>
              <template v-else>
                <button @click="handleLogout" class="btn btn-outline-secondary">로그아웃</button>
              </template>
            </div>
          </div>
        </div>
      </nav>
    </header>

    <main class="flex-grow-1 container my-4 pt-5">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAccountStore } from '@/stores/accounts'
import { useLibraryStore } from '@/stores/library'
import { onMounted, watch } from 'vue'

const store = useAccountStore()
const libraryStore = useLibraryStore()

onMounted(() => {
  if (store.isLogin) {
    libraryStore.fetchLibrary()
  }
})

// 로그인 상태 변경 시 서재 데이터 다시 로드
watch(() => store.isLogin, (newVal) => {
  if (newVal) {
    libraryStore.fetchLibrary()
  }
})

const handleLogout = () => {
  store.logOut()
}
</script>

<style>
/* 기본 부트스트랩 스타일만 사용 */
</style>


