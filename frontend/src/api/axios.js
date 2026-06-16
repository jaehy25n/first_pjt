import axios from 'axios'
import { useAccountStore } from '@/stores/accounts'

const axiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:8000',
})

// Request interceptor to attach Token authentication header
axiosInstance.interceptors.request.use(
  (config) => {
    const accountStore = useAccountStore()
    if (accountStore.token) {
      config.headers.Authorization = `Token ${accountStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default axiosInstance
