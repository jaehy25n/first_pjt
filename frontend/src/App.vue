<template>
  <div id="app-container">
    <header class="top-nav">
      <div class="nav-content">
        <router-link to="/" class="logo">다음책</router-link>
        <nav class="nav-links">
          <router-link to="/" class="nav-item" active-class="active">홈</router-link>
          <router-link to="/search" class="nav-item" active-class="active">검색</router-link>
          <router-link to="/visit" class="nav-item" active-class="active">방문모드</router-link>
          <router-link to="/profile" class="nav-item" active-class="active">프로필</router-link>
        </nav>
        <div class="nav-auth">
          <router-link to="/login" class="login-btn">로그인</router-link>
        </div>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style>
/* Reset and base layout */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: #f8f9fa;
  color: #212529;
}

#app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Navigation bar */
.top-nav {
  position: sticky;
  top: 0;
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e9ecef;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 1.5rem;
  font-weight: 800;
  color: #2b3a4a;
  text-decoration: none;
  background: linear-gradient(45deg, #1e3c72, #2a5298);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.9;
}

.nav-links {
  display: flex;
  gap: 25px;
}

.nav-item {
  font-size: 1rem;
  font-weight: 500;
  color: #495057;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  color: #1e3c72;
  background-color: #f1f3f5;
}

.nav-item.active {
  color: #ffffff;
  background-color: #1e3c72;
}

.nav-auth {
  display: flex;
  align-items: center;
}

.login-btn {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e3c72;
  text-decoration: none;
  padding: 8px 16px;
  border: 1.5px solid #1e3c72;
  border-radius: 20px;
  transition: all 0.2s ease;
}

.login-btn:hover {
  background-color: #1e3c72;
  color: #ffffff;
}

/* Main Content Area */
.main-content {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
}
</style>

