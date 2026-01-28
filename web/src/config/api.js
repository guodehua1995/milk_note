// config/api.js
const config = {
  // 根据环境变量或构建配置来设置API基础URL
  baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json'
  }
}

export default config