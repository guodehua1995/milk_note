// api/index.js
import axios from 'axios'
import config from '../config/api'

// 创建axios实例
const api = axios.create({
  baseURL: config.baseURL,
  timeout: config.timeout,
  headers: config.headers
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从localStorage获取token并添加到请求头
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 处理认证失败等错误
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      // 可以在这里触发登出逻辑
    }
    return Promise.reject(error)
  }
)

export default api