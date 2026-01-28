<template>
  <div class="auth-container">
    <!-- 背景装饰 -->
    <div class="auth-background">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
    
    <!-- 认证卡片 -->
    <div class="auth-card">
      <!-- Logo区域 -->
      <div class="logo-section">
        <h1 class="app-title">MilkNote</h1>
        <p class="app-subtitle">记录灵感，分享生活</p>
      </div>
      
      <!-- 切换按钮 -->
      <div class="auth-toggle">
        <button 
          :class="['toggle-btn', { active: !isLogin }]" 
          @click="switchToRegister"
        >
          注册
        </button>
        <button 
          :class="['toggle-btn', { active: isLogin }]" 
          @click="switchToLogin"
        >
          登录
        </button>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      
      <!-- 表单区域 -->
      <form class="auth-form" @submit.prevent="handleSubmit" novalidate>
        <!-- 用户名 -->
        <div class="form-group">
          <label for="username" class="form-label">用户名</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            class="form-input"
            :class="{ 'is-invalid': errors.username }"
            required
            minlength="3"
            maxlength="20"
            autocomplete="username"
          />
          <div v-if="errors.username" class="invalid-feedback">
            {{ errors.username }}
          </div>
        </div>
        
        <!-- 注册时显示邮箱 -->
        <div v-if="!isLogin" class="form-group">
          <label for="email" class="form-label">邮箱</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱"
            class="form-input"
            :class="{ 'is-invalid': errors.email }"
            required
            autocomplete="email"
          />
          <div v-if="errors.email" class="invalid-feedback">
            {{ errors.email }}
          </div>
        </div>
        
        <!-- 密码 -->
        <div class="form-group">
          <label for="password" class="form-label">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            class="form-input"
            :class="{ 'is-invalid': errors.password }"
            required
            minlength="6"
            maxlength="20"
            autocomplete="current-password"
          />
          <div v-if="errors.password" class="invalid-feedback">
            {{ errors.password }}
          </div>
        </div>
        
        <!-- 注册时显示确认密码 -->
        <div v-if="!isLogin" class="form-group">
          <label for="confirmPassword" class="form-label">确认密码</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            placeholder="请确认密码"
            class="form-input"
            :class="{ 'is-invalid': errors.confirmPassword }"
            required
            minlength="5"
            maxlength="20"
            autocomplete="new-password"
          />
          <div v-if="errors.confirmPassword" class="invalid-feedback">
            {{ errors.confirmPassword }}
          </div>
        </div>
        
        <!-- 登录时显示记住我 -->
        <div v-if="isLogin" class="form-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="rememberMe" id="rememberMe" />
            <span class="checkmark"></span>
            <span>记住我</span>
          </label>
          <a href="#" class="forgot-password">忘记密码？</a>
        </div>
        
        <!-- 提交按钮 -->
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { authAPI } from '../api/auth'

export default {
  name: 'AuthPage',
  data() {
    return {
      isLogin: true, // true为登录，false为注册
      form: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      errors: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      errorMessage: '',
      rememberMe: false,
      loading: false
    }
  },
  methods: {
    switchToLogin() {
      this.isLogin = true
      this.resetErrors()
      this.errorMessage = ''
    },
    switchToRegister() {
      this.isLogin = false
      this.resetErrors()
      this.errorMessage = ''
    },
    resetErrors() {
      this.errors = {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      }
    },
    validateForm() {
      this.resetErrors()
      let isValid = true
      
      // 用户名验证
      if (!this.form.username.trim()) {
        this.errors.username = '请输入用户名'
        isValid = false
      } else if (this.form.username.length < 3) {
        this.errors.username = '用户名长度不能少于3个字符'
        isValid = false
      } else if (this.form.username.length > 20) {
        this.errors.username = '用户名长度不能超过20个字符'
        isValid = false
      }
      
      // 注册时验证邮箱
      if (!this.isLogin) {
        if (!this.form.email.trim()) {
          this.errors.email = '请输入邮箱'
          isValid = false
        } else if (!this.isValidEmail(this.form.email)) {
          this.errors.email = '请输入有效的邮箱地址'
          isValid = false
        }
      }
      
      // 密码验证
      if (!this.form.password) {
        this.errors.password = '请输入密码'
        isValid = false
      } else if (this.form.password.length < 5) {
        this.errors.password = '密码长度不能少于5个字符'
        isValid = false
      } else if (this.form.password.length > 20) {
        this.errors.password = '密码长度不能超过20个字符'
        isValid = false
      }
      
      // 注册时验证确认密码
      if (!this.isLogin) {
        if (!this.form.confirmPassword) {
          this.errors.confirmPassword = '请确认密码'
          isValid = false
        } else if (this.form.password !== this.form.confirmPassword) {
          this.errors.confirmPassword = '两次输入的密码不一致'
          isValid = false
        }
      }
      
      return isValid
    },
    isValidEmail(email) {
      // 简单的邮箱验证正则
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(email)
    },
    async handleSubmit() {
      // 表单验证
      if (!this.validateForm()) {
        return
      }
      
      this.loading = true
      this.errorMessage = ''
      
      try {
        if (this.isLogin) {
          await this.login()
        } else {
          await this.register()
        }
      } catch (error) {
        console.error('认证失败:', error)
        let errorMsg = '操作失败，请重试'
        if (error.response) {
          // 服务器返回了错误响应
          errorMsg = error.response.data.detail || error.response.data.message || errorMsg
        } else if (error.request) {
          // 请求已发出但没有收到响应
          errorMsg = '网络连接失败，请检查网络连接'
        } else {
          // 其他错误
          errorMsg = error.message || errorMsg
        }
        this.errorMessage = errorMsg
      } finally {
        this.loading = false
      }
    },
    async login() {
      const response = await authAPI.login(this.form.username, this.form.password)
      
      // 保存用户信息到localStorage
      if (response.access_token) {
        localStorage.setItem('access_token', response.access_token)
        localStorage.setItem('username', this.form.username)
      }
      
      // 登录成功后跳转到聊天页面
      this.$router.push({ 
        name: 'ChatPage', 
        query: { username: this.form.username || '用户' } 
      })
    },
    async register() {
      await authAPI.register(this.form.username, this.form.email, this.form.password)
      
      this.errorMessage = '注册成功！请登录'
      this.isLogin = true // 自动切换到登录
      // 清空表单
      this.form = {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      }
    }
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.auth-background .circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, #ff9a9e, #fad0c4);
  opacity: 0.1;
}

.auth-background .circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
}

.auth-background .circle-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  right: -50px;
  background: linear-gradient(45deg, #a1c4fd, #c2e9fb);
}

.auth-background .circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  right: 20%;
  background: linear-gradient(45deg, #ffecd2, #fcb69f);
}

.auth-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  position: relative;
  z-index: 10;
}

.logo-section {
  text-align: center;
  margin-bottom: 30px;
}

.app-title {
  font-size: 28px;
  font-weight: 700;
  color: #ff6b6b;
  margin: 0;
  background: linear-gradient(45deg, #ff6b6b, #ffa500);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-subtitle {
  color: #888;
  font-size: 14px;
  margin: 10px 0 0 0;
}

.auth-toggle {
  display: flex;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 30px;
}

.toggle-btn {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-btn.active {
  background: white;
  color: #ff6b6b;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.15);
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  text-align: left;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  font-size: 16px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  outline: none;
  text-align: left;
}

.form-input:focus {
  border-color: #ff6b6b;
  box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
}

.form-input.is-invalid {
  border-color: #ff4d4f;
  box-shadow: 0 0 0 3px rgba(255, 77, 79, 0.1);
}

.invalid-feedback {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #ff4d4f;
  text-align: left;
}

.error-message {
  background-color: #fff2f0;
  color: #ff4d4f;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 14px;
  border: 1px solid #ffccc7;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-size: 14px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #666;
}

.checkbox-label input {
  margin-right: 8px;
}

.forgot-password {
  color: #ff6b6b;
  text-decoration: none;
}

.forgot-password:hover {
  text-decoration: underline;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(45deg, #ff6b6b, #ffa500);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.social-login {
  text-align: center;
}

.divider {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #e9ecef;
}

.divider-text {
  padding: 0 15px;
  color: #888;
  font-size: 14px;
}

.social-buttons {
  display: flex;
  gap: 12px;
}

.social-btn {
  flex: 1;
  padding: 12px;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.social-btn:hover {
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.social-btn.wechat {
  color: #07c160;
  border-color: #07c160;
}

.social-btn.wechat:hover {
  background: rgba(7, 193, 96, 0.05);
}

.social-btn.qq {
  color: #12b7f5;
  border-color: #12b7f5;
}

.social-btn.qq:hover {
  background: rgba(18, 183, 245, 0.05);
}

.social-icon {
  font-size: 18px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .auth-card {
    padding: 30px 20px;
    margin: 0 10px;
  }
  
  .app-title {
    font-size: 24px;
  }
  
  .social-buttons {
    flex-direction: column;
  }
}
</style>
