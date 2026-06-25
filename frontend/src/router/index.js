import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SearchView from '../views/SearchView.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/search',
    name: 'search',
    component: SearchView
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/signup',
    name: 'signup',
    component: () => import('../views/SignupView.vue')
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('../views/OnboardingView.vue')
  },
  {
    path: '/books/:isbn13',
    name: 'book_detail',
    component: () => import('../views/BookDetailView.vue')
  },
  {
    path: '/library',
    name: 'library',
    component: () => import('../views/LibraryView.vue')
  },
  // ── 커뮤니티 ─────────────────────────────────────────────
  {
    path: '/community',
    name: 'community',
    component: () => import('../views/CommunityListView.vue')
  },
  {
    path: '/community/create',
    name: 'community_create',
    component: () => import('../views/CommunityFormView.vue')
  },
  {
    path: '/community/me',
    name: 'community_me',
    component: () => import('../views/CommunityMyView.vue')
  },
  {
    path: '/community/:id',
    name: 'community_detail',
    component: () => import('../views/CommunityDetailView.vue')
  },
  {
    path: '/community/:id/edit',
    name: 'community_edit',
    component: () => import('../views/CommunityFormView.vue')
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
