import { createRouter, createWebHistory } from 'vue-router'
import AuthPage from './components/AuthPage.vue'
import ChatPage from './components/ChatPage.vue'

const routes = [
  {
    path: '/',
    redirect: '/auth'
  },
  {
    path: '/auth',
    name: 'AuthPage',
    component: AuthPage
  },
  {
    path: '/chat',
    name: 'ChatPage',
    component: ChatPage,
    props: route => ({ username: route.query.username || '用户' })
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router