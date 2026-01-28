import { createRouter, createWebHistory } from 'vue-router'
import AuthPage from './components/AuthPage.vue'
import ChatPage from './components/ChatPage.vue'
import KnowledgePage from './components/KnowledgePage.vue'

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
  },
  {
    path: '/knowledge',
    name: 'KnowledgePage',
    component: KnowledgePage,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router