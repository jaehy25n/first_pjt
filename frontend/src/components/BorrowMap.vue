<template>
  <div>
    <!-- 위치 컨트롤 -->
    <div class="d-flex flex-wrap gap-2 align-items-center mb-2">
      <button type="button" class="btn btn-sm btn-outline-primary" :disabled="locating" @click="useMyLocation">
        📍 {{ locating ? '위치 확인 중…' : '내 위치로 보기' }}
      </button>
      <form class="d-flex gap-1" @submit.prevent="geocodeAddress">
        <input
          v-model="addressInput"
          type="text"
          class="form-control form-control-sm"
          style="max-width: 220px;"
          placeholder="또는 내 위치 직접 입력 (예: 마포구 신촌로)"
        />
        <button type="submit" class="btn btn-sm btn-outline-secondary" :disabled="geocoding">찾기</button>
      </form>
      <span v-if="geoMsg" class="text-muted small">{{ geoMsg }}</span>
    </div>

    <!-- 지도 -->
    <div ref="mapEl" class="borrow-map border rounded"></div>

    <!-- 범례 + 요약 -->
    <div class="d-flex flex-wrap gap-3 align-items-center mt-2 small">
      <span><span class="dot" style="background:#2e9e44"></span> 대출 가능</span>
      <span><span class="dot" style="background:#f4b400"></span> 대출 중</span>
      <span><span class="dot" style="background:#5c6bc0"></span> 소장(상태 미확인)</span>
      <span><span class="dot" style="background:#1976d2;border:2px solid #fff;box-shadow:0 0 0 1px #1976d2"></span> 내 위치</span>
      <span class="text-muted ms-auto" v-if="!loading">
        서울 소장 {{ holdingCount }}곳<span v-if="hasLocation"> · 가까운 {{ liveChecked }}곳 실시간 확인</span>
      </span>
    </div>

    <p v-if="!loading && !hasLocation" class="text-muted small mt-1 mb-0">
      '내 위치로 보기'를 누르면 가까운 도서관의 대출 가능 여부를 색으로 표시해요.
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import axiosInstance from '@/api/axios'

const props = defineProps({
  isbn13: { type: String, required: true },
})

// status → 마커 색 + 라벨 (백엔드 borrow_map과 어휘 통일, D36)
const STATUS = {
  available:    { fill: '#2e9e44', stroke: '#1b7a33', label: '대출 가능' },
  loaned:       { fill: '#f4b400', stroke: '#b8860b', label: '대출 중' },
  held_unknown: { fill: '#5c6bc0', stroke: '#3949ab', label: '소장(상태 미확인)' },
}
const SEOUL = [37.5665, 126.9780]

const mapEl = ref(null)
const loading = ref(true)
const locating = ref(false)
const geocoding = ref(false)
const geoMsg = ref('')
const addressInput = ref('')
const hasLocation = ref(false)
const holdingCount = ref(0)
const liveChecked = ref(0)

// Leaflet 객체는 reactive로 만들지 않음(프록시가 내부 동작을 깨뜨림)
let map = null
let libLayer = null
let userMarker = null
let userLatLng = null

const initMap = () => {
  map = L.map(mapEl.value, { scrollWheelZoom: true }).setView(SEOUL, 12)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap',
  }).addTo(map)
  libLayer = L.layerGroup().addTo(map)
  setTimeout(() => map && map.invalidateSize(), 0)
}

const fetchAndRender = async (lat = null, lng = null) => {
  loading.value = true
  userLatLng = lat != null && lng != null ? [lat, lng] : null
  try {
    const params = userLatLng ? { lat, lng } : {}
    const res = await axiosInstance.get(`/api/books/${props.isbn13}/borrow-map/`, { params })
    const d = res.data
    hasLocation.value = !!d.has_location
    holdingCount.value = d.holding_count || 0
    liveChecked.value = d.live_checked || 0
    renderMarkers(d.libraries || [])
  } catch (e) {
    console.error('지도 데이터 로드 실패:', e)
  } finally {
    loading.value = false
  }
}

const renderMarkers = (libraries) => {
  if (!map) return
  libLayer.clearLayers()
  const holdingPts = [] // 소장관 좌표 (거리순). 미소장(none)은 제외.

  for (const lib of libraries) {
    if (lib.status === 'none') continue // 미소장은 표시하지 않음
    if (lib.latitude == null || lib.longitude == null) continue
    const s = STATUS[lib.status] || STATUS.held_unknown
    const ll = [lib.latitude, lib.longitude]
    holdingPts.push(ll)
    const dist = lib.distance_km != null ? ` · ${lib.distance_km}km` : ''
    L.circleMarker(ll, {
      radius: 7, weight: 2, color: s.stroke, fillColor: s.fill, fillOpacity: 0.9,
    })
      .bindPopup(`<strong>${lib.name || ''}</strong><br>${s.label}${dist}` +
                 (lib.address ? `<br><small>${lib.address}</small>` : ''))
      .addTo(libLayer)
  }

  // 내 위치 마커
  if (userMarker) { map.removeLayer(userMarker); userMarker = null }
  if (userLatLng) {
    userMarker = L.marker(userLatLng, {
      icon: L.divIcon({ className: 'user-pin', html: '<div class="user-dot"></div>', iconSize: [16, 16], iconAnchor: [8, 8] }),
      zIndexOffset: 1000,
    }).bindPopup('내 위치').addTo(map)
  }

  // 줌: 위치를 주면(검색/내위치) 그 지점 중심으로 적당히 확대 = 내 위치 + 가장 가까운 소장관.
  //     위치가 없으면 소장관 전체가 보이게.
  if (userLatLng) {
    const nearest = holdingPts[0] // libraries는 거리순 → 첫 소장 마커가 최근접
    if (nearest) {
      map.fitBounds(L.latLngBounds([userLatLng, nearest]).pad(0.5), { maxZoom: 12 })
    } else {
      map.setView(userLatLng, 12)
    }
  } else if (holdingPts.length > 1) {
    map.fitBounds(L.latLngBounds(holdingPts).pad(0.2), { maxZoom: 15 })
  } else if (holdingPts.length === 1) {
    map.setView(holdingPts[0], 14)
  }
}

const useMyLocation = () => {
  geoMsg.value = ''
  if (!navigator.geolocation) {
    geoMsg.value = '이 브라우저는 위치를 지원하지 않아요. 주소를 입력해 주세요.'
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      locating.value = false
      fetchAndRender(pos.coords.latitude, pos.coords.longitude)
    },
    () => {
      locating.value = false
      geoMsg.value = '위치 권한이 꺼져 있어요. 주소를 입력해 주세요.'
    },
    { timeout: 8000 }
  )
}

const geocodeAddress = async () => {
  const q = addressInput.value.trim()
  if (!q) return
  geoMsg.value = ''
  geocoding.value = true
  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=kr&q=${encodeURIComponent(q)}`
    const res = await fetch(url, { headers: { 'Accept-Language': 'ko' } })
    const data = await res.json()
    if (Array.isArray(data) && data.length > 0) {
      await fetchAndRender(parseFloat(data[0].lat), parseFloat(data[0].lon))
    } else {
      geoMsg.value = '주소를 찾지 못했어요. 더 구체적으로 입력해 주세요.'
    }
  } catch (e) {
    geoMsg.value = '주소 검색에 실패했어요.'
  } finally {
    geocoding.value = false
  }
}

onMounted(() => {
  initMap()
  fetchAndRender()
})

onBeforeUnmount(() => {
  if (map) { map.remove(); map = null }
})
</script>

<style scoped>
.borrow-map {
  height: 380px;
  width: 100%;
}
.dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  vertical-align: -1px;
  margin-right: 2px;
}
/* 내 위치 핀 (divIcon 내부) */
:deep(.user-dot) {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #1976d2;
  border: 3px solid #fff;
  box-shadow: 0 0 0 2px #1976d2;
}
</style>
