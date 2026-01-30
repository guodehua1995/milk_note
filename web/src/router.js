import { createRouter, createWebHistory } from 'vue-router'
import AuthPage from './components/AuthPage.vue'
import ChatPage from './components/ChatPage.vue'
import KnowledgePage from './components/KnowledgePage.vue'
import TaskPage from './components/TaskPage.vue'
import TaskDetail from './components/TaskDetail.vue'
import RecurringTaskDetail from './components/RecurringTaskDetail.vue'
import OKRDetail from './components/OKRDetail.vue'

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
    name: 'TaskDetail',
    component: TaskDetail,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  },
  {
    path: '/recurring-task-detail/:id',
    name: 'RecurringTaskDetail',
    component: RecurringTaskDetail,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  },
  {
    path: '/okr-detail/:id',
    name: 'OKRDetail',
    component: OKRDetail,
    props: () => ({ username: localStorage.getItem('username') || '用户' })
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router