// api/auth.js
import api from './index'

export const authAPI = {
  // 用户注册
  register: (username, email, password) => {
    return api.post('/auth/register', {
      username,
      email,
      password
    })
  },

  // 用户登录
  login: (username, password) => {
    return api.post('/auth/login', {
      username,
      password
    })
  },

  // 获取当前用户信息
  getCurrentUser: () => {
    return api.get('/users/me')
  },

  // 刷新token
  refreshToken: () => {
    return api.post('/auth/refresh')
  }
}