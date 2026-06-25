<template>
  <div id="app-container" class="d-flex flex-column min-vh-100 position-relative">
    <!-- 은은한 오로라 배경 (홈 화면 전용) -->
    <div v-if="isHome" class="aurora-background position-fixed w-100 h-100" style="z-index: 0;">
      <div class="aurora-blob aurora-1"></div>
      <div class="aurora-blob aurora-2"></div>
      <div class="aurora-blob aurora-3"></div>
    </div>

    <header>
      <!-- Collapsing Glassmorphism Header -->
      <nav class="navbar fixed-top p-0" :style="navContainerStyle">
        
        <div class="container position-relative w-100 h-100">
          
          <!-- 네비게이션 링크들 (우측 상단에 고정) -->
          <div class="position-absolute end-0 pe-3 d-flex align-items-center" style="top: 18px; z-index: 1040;">
            <ul class="navbar-nav flex-row me-3 d-none d-md-flex align-items-center">
              <li class="nav-item me-3"><router-link to="/" class="nav-link text-dark fw-bold">홈</router-link></li>
              <li class="nav-item me-3"><router-link to="/search" class="nav-link text-dark fw-bold">검색</router-link></li>
              <li class="nav-item me-3"><router-link to="/community" class="nav-link text-dark fw-bold">커뮤니티</router-link></li>
              <li class="nav-item" v-if="store.isLogin"><router-link to="/library" class="nav-link text-dark fw-bold">내 서재</router-link></li>
            </ul>
            <div class="d-flex align-items-center">
              <template v-if="!store.isLogin">
                <router-link to="/login" class="btn btn-outline-primary btn-sm me-2 fw-bold">로그인</router-link>
                <router-link to="/signup" class="btn btn-primary btn-sm fw-bold">회원가입</router-link>
              </template>
              <template v-else>
                <button @click="handleLogout" class="btn btn-outline-secondary btn-sm fw-bold">로그아웃</button>
              </template>
            </div>
          </div>

          <!-- 로고 -->
          
          <router-link to="/" class="navbar-brand d-flex align-items-center position-absolute m-0 text-decoration-none"
                       :style="logoContainerStyle">
            <img src="@/assets/logo.png" alt="책잇다 로고" :style="logoImgStyle" class="me-2" />
          </router-link>

          <!-- 센스있는 서브타이틀 (점점 페이드아웃) -->
          <p class="position-absolute text-muted mb-0" v-if="isHome" :style="subtitleStyle">
            당신의 일상과 도서관을 잇는<br>단 하나의 책갈피
          </p>

          <!-- 스크롤 유도 인디케이터 (래퍼로 분리하여 CSS 애니메이션과 충돌 방지, 하단에 고정) -->
          <div class="position-absolute" v-if="isHome" :style="scrollIndicatorWrapperStyle">
            <div class="text-muted d-flex flex-column align-items-center scroll-indicator">
              <span class="small mb-2" style="letter-spacing: 0.1em; font-weight: 500;">Scroll to Explore</span>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="bouncing-icon"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
          </div>
          
        </div>
      </nav>
    </header>

    <!-- 메인 콘텐츠 -->
    <!-- 홈 화면에서는 80vh부터 시작하게 하여 하단 20vh 정도가 100vh 네비게이션 아래로 블러 처리되어 비치게 만듦 -->
    <main class="flex-grow-1" :style="{ paddingTop: isHome ? '80vh' : '100px' }" :class="{ 'container': $route.path !== '/' }">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAccountStore } from '@/stores/accounts'
import { useLibraryStore } from '@/stores/library'
import { onMounted, onUnmounted, watch, ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const store = useAccountStore()
const libraryStore = useLibraryStore()
const route = useRoute()

const isHome = computed(() => route.path === '/')
const windowHeight = ref(window.innerHeight)
const scrollY = ref(0)

const handleScroll = () => {
  scrollY.value = window.scrollY
}
const handleResize = () => {
  windowHeight.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('resize', handleResize)
  if (store.isLogin) {
    libraryStore.fetchLibrary()
  }
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', handleResize)
})

const maxNavHeight = computed(() => isHome.value ? windowHeight.value : 70)
const minNavHeight = 70

const currentNavHeight = computed(() => {
  if (!isHome.value) return minNavHeight
  // 스크롤 시 헤더가 줄어드는 속도 (콘텐츠가 따라 올라오며 나타남)
  const h = maxNavHeight.value - (scrollY.value * 1.5)
  return Math.max(minNavHeight, h)
})

const isCollapsed = computed(() => currentNavHeight.value <= minNavHeight)

const collapseRatio = computed(() => {
  if (!isHome.value) return 1
  const range = maxNavHeight.value - minNavHeight
  if (range <= 0) return 1
  return Math.min(1, Math.max(0, (scrollY.value * 1.5) / range))
})

// 동적 스타일
const navContainerStyle = computed(() => {
  // 스크롤 할수록 투명도가 줄어들며 하얀색으로 변함
  const bgAlpha = 0.5 + (0.5 * collapseRatio.value);
  return {
    height: currentNavHeight.value + 'px',
    background: isCollapsed.value ? 'rgba(255,255,255,1)' : `rgba(255,255,255,${bgAlpha})`,
    backdropFilter: isCollapsed.value ? 'none' : 'blur(15px)',
    WebkitBackdropFilter: isCollapsed.value ? 'none' : 'blur(15px)',
    borderBottom: isCollapsed.value ? '1px solid #dee2e6' : 'none',
    boxShadow: isCollapsed.value ? '0 0.125rem 0.25rem rgba(0,0,0,0.075)' : 'none',
    transition: 'background 0s, height 0s', // JS 기반 동적 랜더링이므로 CSS transition 제거
    zIndex: 1030
  }
})

const logoContainerStyle = computed(() => {
  const leftPos = isCollapsed.value ? '0%' : `${50 - (50 * collapseRatio.value)}%`;
  const translateX = isCollapsed.value ? '0%' : `-${50 - (50 * collapseRatio.value)}%`;
  
  // 시작 지점: 화면 중앙 (100vh의 절반), 끝 지점: 35px (70px 헤더의 중앙)
  const startTop = windowHeight.value / 2 - 100;
  const endTop = 35;
  const currentTop = startTop - ((startTop - endTop) * collapseRatio.value);

  return {
    top: currentTop + 'px',
    left: leftPos,
    transform: `translate(${translateX}, -50%)`,
    transition: 'none'
  }
})

const logoImgStyle = computed(() => {
  const maxSize = 400;
  const minSize = 50;
  const size = maxSize - ((maxSize - minSize) * collapseRatio.value);
  return {
    height: size + 'px',
    width: size + 'px',
    objectFit: 'contain'
  }
})

const logoTextStyle = computed(() => {
  const maxFs = 4.5;
  const minFs = 1.5;
  const fs = maxFs - ((maxFs - minFs) * collapseRatio.value);
  const maxLs = -0.05;
  const minLs = 0;
  const ls = maxLs - ((maxLs - minLs) * collapseRatio.value);
  return {
    fontSize: fs + 'rem',
    letterSpacing: ls + 'em'
  }
})

const subtitleStyle = computed(() => {
  // 로고 바로 아래에 위치
  const startTop = (windowHeight.value / 2) + 50; 
  const endTop = 35 + 90;
  const currentTop = startTop - ((startTop - endTop) * collapseRatio.value);

  return {
    top: currentTop + 'px',
    left: '50%',
    transform: 'translateX(-50%)',
    opacity: Math.max(0, 1 - (collapseRatio.value * 2.5)), // 더 빨리 페이드아웃
    display: collapseRatio.value > 0.4 ? 'none' : 'block',
    letterSpacing: '0.1em',
    fontWeight: 600,
    fontSize: '1.25rem',
    whiteSpace: 'normal',
    textAlign: 'center',
    width: '100%',
    color: '#6c757d'
  }
})

const scrollIndicatorWrapperStyle = computed(() => {
  // 스크롤 시작 즉시(50px 이내) 빠르게 완전히 페이드아웃
  const fadeOpacity = Math.max(0, 1 - (scrollY.value / 50));
  return {
    bottom: '40px',
    left: '50%',
    transform: 'translateX(-50%)',
    opacity: fadeOpacity,
    display: fadeOpacity === 0 ? 'none' : 'block'
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
/* App 전역 스타일 */
.nav-link:hover {
  color: var(--bs-primary) !important;
}

/* 오로라 배경 애니메이션 */
.aurora-background {
  overflow: hidden;
  pointer-events: none;
  background-color: #f8f9fa; /* 매우 밝은 회색/흰색 베이스 */
}
.aurora-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 20s infinite alternate ease-in-out;
}
.aurora-1 {
  width: 40vw; height: 40vw;
  background-color: rgba(13, 110, 253, 0.15); /* 파란색 */
  top: -10%; left: -10%;
}
.aurora-2 {
  width: 50vw; height: 50vw;
  background-color: rgba(111, 66, 193, 0.1); /* 보라색 */
  bottom: -10%; right: -10%;
  animation-delay: -5s;
}
.aurora-3 {
  width: 35vw; height: 35vw;
  background-color: rgba(20, 164, 77, 0.1); /* 에메랄드/초록색 */
  top: 40%; left: 40%;
  animation-delay: -10s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(3vw, -5vh) scale(1.1); }
  66% { transform: translate(-2vw, 2vh) scale(0.9); }
  100% { transform: translate(0, 0) scale(1); }
}

/* 스크롤 인디케이터 애니메이션 */
.scroll-indicator {
  animation: fadeIn 2s ease-in 1s both;
}
.bouncing-icon {
  animation: bounce 2s infinite;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-10px); }
  60% { transform: translateY(-5px); }
}
</style>
