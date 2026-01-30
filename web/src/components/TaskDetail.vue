<template>
  <div class="task-detail-page">
    <!-- 工具栏 -->
    <Toolbar :username="username" />
    
    <!-- 页面内容 -->
    <div class="page-content">
      <div class="page-header">
        <h1>任务详情</h1>
        <button @click="goBack" class="btn-secondary">返回</button>
      </div>
      
      <div v-if="task" class="task-detail-card">
        <div class="card-header" :class="task.status">
          <h2>{{ task.title }}</h2>
          <div :class="['priority-indicator', task.priority]">
            <span class="priority-text">{{ getPriorityText(task.priority) }}</span>
          </div>
        </div>
        <div class="card-body">
          <p v-if="task.description" class="task-description">{{ task.description }}</p>
          <div class="task-meta">
            <div class="meta-item">
              <span class="meta-label">状态：</span>
              <span :class="['status-badge', task.status]">{{ getStatusText(task.status) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">优先级：</span>
              <span :class="['priority-badge', task.priority]">{{ getPriorityText(task.priority) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">开始时间：</span>
              <span>{{ formatDate(task.start_time) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">结束时间：</span>
              <span>{{ formatDate(task.end_time) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建时间：</span>
              <span>{{ formatDate(task.created_at) }}</span>
            </div>
          </div>
        </div>
        <div class="card-footer">
          <button @click="editTask(task)" class="btn-complete">编辑</button>
          <button @click="deleteTask(task.id)" class="btn-cancel">删除</button>
          <button v-if="task.status !== 'completed'" @click="completeTask(task.id)" class="btn-complete">标记完成</button>
        </div>
      </div>
      <div v-else class="empty-state">
        任务不存在或已被删除
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Toolbar from './Toolbar.vue'
import '../styles/dialog.css'

export default {
  name: 'TaskDetail',
  components: {
    Toolbar
  },
  props: {
    username: {
      type: String,
      default: '用户'
    }
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const task = ref(null)
    
    // 获取任务详情
    const fetchTaskDetail = async () => {
      try {
        const taskId = route.params.id
        // 这里需要添加获取任务详情的API调用
        // 暂时使用假数据
        task.value = {
          id: taskId,
          title: '示例任务',
          description: '这是一个示例任务的详细描述',
          status: 'in_progress',
          priority: 'medium',
          start_time: new Date(),
          end_time: new Date(Date.now() + 86400000),
          created_at: new Date()
        }
      } catch (error) {
        console.error('获取任务详情失败:', error)
      }
    }
    
    // 返回上一页
    const goBack = () => {
      router.push('/tasks')
    }
    
    // 编辑任务
    const editTask = (task) => {
      console.log('编辑任务:', task)
    }
    
    // 删除任务
    const deleteTask = (taskId) => {
      if (confirm('确定要删除这个任务吗？')) {
        console.log('删除任务:', taskId)
        router.push('/tasks')
      }
    }
    
    // 标记任务完成
    const completeTask = (taskId) => {
      console.log('标记任务完成:', taskId)
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        not_started: '未开始',
        in_progress: '进行中',
        completed: '已完成',
        cancelled: '已取消',
        overdue: '已过期'
      }
      return statusMap[status] || status
    }
    
    // 获取优先级文本
    const getPriorityText = (priority) => {
      const priorityMap = {
        low: '低',
        medium: '中',
        high: '高'
      }
      return priorityMap[priority] || priority
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    // 组件挂载时获取任务详情
    onMounted(async () => {
      await fetchTaskDetail()
    })
    
    return {
      task,
      goBack,
      editTask,
      deleteTask,
      completeTask,
      getStatusText,
      getPriorityText,
      formatDate
    }
  }
}
</script>

<style scoped>
.task-detail-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
}

.page-content {
  padding: 80px 20px 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
  font-weight: 600;
}

.task-detail-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  margin-bottom: 20px;
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
  font-weight: 600;
  flex: 1;
}

.card-body {
  padding: 20px;
}

.task-description {
  font-size: 16px;
  line-height: 1.5;
  color: #666;
  margin-bottom: 20px;
}

.task-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  min-width: 80px;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px 20px;
  border-top: 1px solid #f0f0f0;
  background-color: #f9f9f9;
}

.empty-state {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 40px;
  text-align: center;
  color: #666;
  font-size: 16px;
}
</style>
