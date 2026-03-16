import { createRouter, createWebHistory } from 'vue-router'
import AuthPage from './components/AuthPage.vue'
import ChatPage from './components/ChatPage.vue'
import KnowledgePage from './components/KnowledgePage.vue'
import TaskPage from './components/TaskPage.vue'
import TaskDetailOnce from './components/TaskDetailOnce.vue'
import TaskDetailRepeat from './components/TaskDetailRepeat.vue'
import TaskDetailComplex from './components/TaskDetailComplex.vue'

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
  },
  {
    path: '/tasks',
    name: 'TaskPage',
    component: TaskPage,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  },
  {
    path: '/task-detail/:id',
    name: 'TaskDetailOnce',
    component: TaskDetailOnce,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  },
  {
    path: '/recurring-task-detail/:id',
    name: 'TaskDetailRepeat',
    component: TaskDetailRepeat,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  },
  {
    path: '/okr-detail/:id',
    name: 'TaskDetailComplex',
    component: TaskDetailComplex,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router