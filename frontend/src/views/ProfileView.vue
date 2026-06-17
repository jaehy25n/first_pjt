<template>
  <div class="container py-4">
    <h2 class="fw-bold text-primary logo-gradient mb-4">온보딩 & 프로필 설정</h2>
    
    <div class="row g-4">
      <!-- 관심사 설정 섹션 -->
      <div class="col-lg-6">
        <div class="card shadow-sm border-0 rounded-4 h-100">
          <div class="card-body p-4">
            <h4 class="fw-bold mb-3">1. 관심사 선택</h4>
            <p class="text-muted mb-4">자주 읽거나 관심 있는 분야를 선택해주세요. (다중 선택 가능)</p>
            
            <div class="d-flex flex-wrap gap-2">
              <button 
                v-for="interest in allInterests" 
                :key="interest.id"
                @click="toggleInterest(interest.id)"
                class="btn rounded-pill px-4 py-2 transition-all"
                :class="selectedInterests.includes(interest.id) ? 'btn-primary shadow' : 'btn-outline-secondary bg-light text-dark border-0'"
              >
                {{ interest.name }}
              </button>
            </div>
            
            <div v-if="allInterests.length === 0" class="text-center text-muted py-3">
              <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
              관심사 목록을 불러오는 중입니다...
            </div>
          </div>
        </div>
      </div>

      <!-- 주 도서관 설정 섹션 -->
      <div class="col-lg-6">
        <div class="card shadow-sm border-0 rounded-4 h-100">
          <div class="card-body p-4">
            <h4 class="fw-bold mb-3">2. 주 도서관 설정</h4>
            <p class="text-muted mb-4">가장 자주 이용하는 도서관을 검색하고 선택해주세요.</p>
            
            <form @submit.prevent="searchLibraries" class="d-flex gap-2 mb-3">
              <input 
                type="text" 
                class="form-control bg-light border-0" 
                v-model.trim="searchQuery" 
                placeholder="도서관 이름 (예: 마포)"
              >
              <button type="submit" class="btn btn-dark px-4 rounded" :disabled="isSearching">
                <span v-if="isSearching" class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                <span v-else>검색</span>
              </button>
            </form>

            <!-- 선택된 도서관 표시 -->
            <div v-if="selectedLibrary" class="alert alert-primary mb-3 d-flex justify-content-between align-items-center">
              <div>
                <strong>현재 선택됨:</strong> {{ selectedLibrary.name || selectedLibrary.library_name }}
              </div>
            </div>

            <!-- 검색 결과 목록 -->
            <div class="list-group list-group-flush border rounded-3" style="max-height: 250px; overflow-y: auto;">
              <button 
                v-for="lib in searchResults" 
                :key="lib.lib_code"
                type="button"
                @click="selectLibrary(lib)"
                class="list-group-item list-group-item-action py-3 d-flex flex-column transition-all"
                :class="{ 'bg-primary-subtle border-primary': selectedLibrary?.lib_code === lib.lib_code }"
              >
                <span class="fw-bold text-dark">{{ lib.name }}</span>
                <small class="text-muted">{{ lib.region }}</small>
              </button>
              
              <div v-if="hasSearched && searchResults.length === 0" class="text-center text-muted py-4">
                검색 결과가 없습니다.
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

    <!-- 저장 버튼 -->
    <div class="mt-5 text-center">
      <div v-if="saveMessage" class="alert mb-4 d-inline-block px-5" :class="saveStatus ? 'alert-success' : 'alert-danger'">
        {{ saveMessage }}
      </div>
      <div>
        <button @click="saveProfile" class="btn btn-primary btn-lg rounded-pill px-5 shadow" :disabled="isSaving">
          <span v-if="isSaving" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
          {{ isSaving ? '저장 중...' : '프로필 저장완료' }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axiosInstance from '@/api/axios'

// State
const allInterests = ref([])
const selectedInterests = ref([])

const searchQuery = ref('')
const searchResults = ref([])
const selectedLibrary = ref(null)
const hasSearched = ref(false)
const isSearching = ref(false)

const isSaving = ref(false)
const saveMessage = ref('')
const saveStatus = ref(true) // true for success, false for error

// Fetch initial profile & interests
onMounted(async () => {
  try {
    // 1. 관심사 목록 불러오기
    const interestsRes = await axiosInstance.get('/api/interests/')
    allInterests.value = interestsRes.data

    // 2. 내 프로필 불러와서 초기값 세팅하기
    const profileRes = await axiosInstance.get('/api/profile/')
    const profile = profileRes.data
    
    if (profile.interests) {
      selectedInterests.value = profile.interests.map(i => i.id)
    }
    if (profile.primary_library) {
      selectedLibrary.value = profile.primary_library
    }
  } catch (error) {
    console.error('초기 데이터 로드 실패:', error)
  }
})

// 관심사 선택 토글
const toggleInterest = (id) => {
  const index = selectedInterests.value.indexOf(id)
  if (index === -1) {
    selectedInterests.value.push(id)
  } else {
    selectedInterests.value.splice(index, 1)
  }
}

// 도서관 검색
const searchLibraries = async () => {
  if (!searchQuery.value) return
  
  isSearching.value = true
  hasSearched.value = false
  saveMessage.value = ''
  
  try {
    const res = await axiosInstance.get(`/api/libraries/?q=${encodeURIComponent(searchQuery.value)}`)
    searchResults.value = res.data
    hasSearched.value = true
  } catch (error) {
    console.error('도서관 검색 실패:', error)
  } finally {
    isSearching.value = false
  }
}

// 도서관 선택
const selectLibrary = (lib) => {
  selectedLibrary.value = lib
  saveMessage.value = ''
}

// 프로필 저장 (온보딩)
const saveProfile = async () => {
  isSaving.value = true
  saveMessage.value = ''
  
  try {
    const payload = {
      interest_ids: selectedInterests.value,
      primary_library_code: selectedLibrary.value ? selectedLibrary.value.lib_code : null
    }
    
    await axiosInstance.patch('/api/profile/onboarding/', payload)
    
    saveStatus.value = true
    saveMessage.value = '프로필이 성공적으로 저장되었습니다!'
    
    // 메시지 3초 뒤 숨기기
    setTimeout(() => {
      saveMessage.value = ''
    }, 3000)
    
  } catch (error) {
    console.error('프로필 저장 실패:', error)
    saveStatus.value = false
    saveMessage.value = '저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.transition-all {
  transition: all 0.2s ease-in-out;
}
.btn-outline-secondary:hover {
  background-color: #e9ecef !important;
  color: #000 !important;
  transform: translateY(-2px);
}
.list-group-item:hover {
  background-color: #f8f9fa;
  cursor: pointer;
}
.bg-primary-subtle {
  background-color: #cfe2ff !important;
}
</style>
