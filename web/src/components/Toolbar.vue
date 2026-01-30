<template>
  <div class="toolbar">
    <div class="toolbar-logo">
      <img src="@/assets/ScreenShot_2026-01-29_162557_067.png" alt="Logo" class="logo" />
      <h1>通用智能助手</h1>
    </div>
    <div class="toolbar-menu">
      <router-link to="/chat" class="menu-item" :class="{ active: $route.path === '/chat' }">
        <i class="menu-icon chat-icon"></i>
        <span>聊天</span>
      </router-link>
      <router-link to="/knowledge" class="menu-item" :class="{ active: $route.path === '/knowledge' || $route.path.startsWith('/knowledge/') }">
        <i class="menu-icon knowledge-icon"></i>
        <span>知识库管理</span>
      </router-link>
      <router-link to="/tasks" class="menu-item" :class="{ active: $route.path === '/tasks' }">
        <i class="menu-icon task-icon"></i>
        <span>任务管理</span>
      </router-link>
    </div>
    <div class="toolbar-user">
      <span class="username">{{ username }}</span>
      <button class="logout-btn" @click="handleLogout">退出</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppToolbar',
  props: {
    username: {
      type: String,
      default: '用户'
    }
  },
  methods: {
    handleLogout() {
      // 清除本地存储的认证信息
      localStorage.removeItem('token');
      localStorage.removeItem('userInfo');
      // 跳转到登录页
      this.$router.push('/auth');
    }
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #ffffff;
  border-bottom: 1px solid #eaeaea;
  padding: 0 20px;
  height: 60px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.toolbar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  height: 40px;
  width: 40px;
  object-fit: contain;
}

.toolbar-logo h1 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.toolbar-menu {
  display: flex;
  gap: 20px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  color: #666;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background-color: #f5f5f5;
  color: #333;
}

.menu-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
}

.menu-icon {
  width: 16px;
  height: 16px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

/* 使用简单的文字图标替代，实际项目中可以使用SVG或图标库 */
.chat-icon::before {
  content: "💬";
  font-size: 18px;
}

.knowledge-icon::before {
  content: "📚";
  font-size: 18px;
}

.task-icon::before {
  content: "✅";
  font-size: 18px;
}

.toolbar-user {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.logout-btn {
  padding: 6px 12px;
  background-color: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.logout-btn:hover {
  background-color: #ff7875;
}
</style>