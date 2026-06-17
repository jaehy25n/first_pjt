<template>
  <div class="container py-4">
    <h2>온보딩 & 프로필 설정</h2>
    
    <div class="row g-4 mt-2">
      <!-- 관심사 설정 섹션 -->
      <div class="col-lg-6">
        <div class="card h-100">
          <div class="card-body">
            <h4>1. 관심사 선택</h4>
            <p>자주 읽거나 관심 있는 분야를 선택해주세요. (다중 선택 가능)</p>
            
            <div class="d-flex flex-wrap gap-2">
              <button 
                v-for="interest in allInterests" 
                :key="interest.id"
                @click="toggleInterest(interest.id)"
                class="btn"
                :class="selectedInterests.includes(interest.id) ? 'btn-primary' : 'btn-outline-secondary'"
              >
                {{ interest.name }}
              </button>
            </div>
            
            <div v-if="allInterests.length === 0" class="text-center py-3">
              <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
              관심사 목록을 불러오는 중입니다...
            </div>
          </div>
        </div>
      </div>

      <!-- 주 도서관 설정 섹션 -->
      <div class="col-lg-6">
        <div class="card h-100">
          <div class="card-body">
            <h4>2. 주 도서관 설정</h4>
            <p>가장 자주 이용하는 도서관을 검색하고 선택해주세요.</p>
            
            <form @submit.prevent="searchLibraries" class="d-flex gap-2 mb-3">
              <input 
                type="text" 
                class="form-control" 
                v-model.trim="searchQuery" 
                placeholder="도서관 이름 (예: 마포)"
              >
              <button type="submit" class="btn btn-secondary" :disabled="isSearching">
                <span v-if="isSearching" class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                <span v-else>검색</span>
              </button>
            </form>

            <!-- 선택된 도서관 표시 -->
            <div v-if="selectedLibrary" class="alert alert-info mb-3">
              <strong>현재 선택됨:</strong> {{ selectedLibrary.name || selectedLibrary.library_name }}
            </div>

            <!-- 검색 결과 목록 -->
            <div class="list-group" style="max-height: 250px; overflow-y: auto;">
              <button 
                v-for="lib in searchResults" 
                :key="lib.lib_code"
                type="button"
                @click="selectLibrary(lib)"
                class="list-group-item list-group-item-action"
                :class="{ 'active': selectedLibrary?.lib_code === lib.lib_code }"
              >
                <span>{{ lib.name }}</span>
                <small class="d-block">{{ lib.region }}</small>
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
        <button @click="saveProfile" class="btn btn-primary btn-lg rounded-pill px-5 shadow-sm" :disabled="isSaving">
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
const saveStatus = ref(true)

onMounted(async () => {
  try {
    const interestsRes = await axiosInstance.get('/api/interests/')
    allInterests.value = interestsRes.data

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

const toggleInterest = (id) => {
  const index = selectedInterests.value.indexOf(id)
  if (index === -1) {
    selectedInterests.value.push(id)
  } else {
    selectedInterests.value.splice(index, 1)
  }
}

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

const selectLibrary = (lib) => {
  selectedLibrary.value = lib
  saveMessage.value = ''
}

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
