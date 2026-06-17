<template>
  <div id="app-container" class="d-flex flex-column min-vh-100 bg-light">
    <header>
      <nav class="navbar navbar-expand-md navbar-light bg-white border-bottom sticky-top shadow-sm">
        <div class="container">
          <router-link to="/" class="navbar-brand fw-bold fs-3 text-primary logo-gradient">다음책</router-link>
          
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent" aria-controls="navbarContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          
          <div class="collapse navbar-collapse" id="navbarContent">
            <ul class="navbar-nav me-auto mb-2 mb-md-0 gap-md-2">
              <li class="nav-item">
                <router-link to="/" class="nav-link px-3 rounded" active-class="active text-white bg-primary">홈</router-link>
              </li>
              <li class="nav-item">
                <router-link to="/search" class="nav-link px-3 rounded" active-class="active text-white bg-primary">검색</router-link>
              </li>
              <li class="nav-item">
                <router-link to="/visit" class="nav-link px-3 rounded" active-class="active text-white bg-primary">방문모드</router-link>
              </li>
              <li class="nav-item" v-if="store.isLogin">
                <router-link to="/profile" class="nav-link px-3 rounded" active-class="active text-white bg-primary">프로필</router-link>
              </li>
            </ul>
            <div class="d-flex align-items-center mt-2 mt-md-0 gap-2">
              <template v-if="!store.isLogin">
                <router-link to="/login" class="btn btn-outline-primary px-4 rounded-pill">로그인</router-link>
                <router-link to="/signup" class="btn btn-primary px-4 rounded-pill shadow-sm">회원가입</router-link>
              </template>
              <template v-else>
                <button @click="handleLogout" class="btn btn-outline-secondary px-4 rounded-pill">로그아웃</button>
              </template>
            </div>
          </div>
        </div>
      </nav>
    </header>

    <main class="flex-grow-1 container my-4">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAccountStore } from '@/stores/accounts'

const store = useAccountStore()

const handleLogout = () => {
  store.logOut()
}
</script>

<style>
/* Reset global defaults if any, let Bootstrap handle base typography */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.logo-gradient {
  background: linear-gradient(45deg, #1e3c72, #2a5298);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>


