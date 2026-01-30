<template>
  <div class="recurring-task-detail-page">
    <!-- 工具栏 -->
    <Toolbar :username="username" />
    
    <!-- 页面内容 -->
    <div class="page-content">
      <div class="page-header">
        <h1>重复任务详情</h1>
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
              <span class="meta-label">重复类型：</span>
              <span>{{ getRecurrenceText(task) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建时间：</span>
              <span>{{ formatDate(task.created_at) }}</span>
            </div>
          </div>
          
          <!-- 任务实例列表 -->
          <div class="task-instances-list">
            <h3>任务实例</h3>
            <div v-if="taskInstances.length === 0" class="empty-state">
              暂无任务实例
            </div>
            <div v-else class="instance-cards">
              <div v-for="instance in taskInstances" :key="instance.id" class="instance-card">
                <div class="instance-header">
                  <h4>{{ instance.title }}</h4>
                  <span :class="['status-badge', instance.status]">{{ getStatusText(instance.status) }}</span>
                </div>
                <div class="instance-body">
                  <p v-if="instance.description">{{ instance.description }}</p>
                  <div class="instance-time">
                    <span class="time-badge">{{ formatDate(instance.start_time) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="card-footer">
          <button @click="editTask(task)" class="btn-complete">编辑</button>
          <button @click="deleteTask(task.id)" class="btn-cancel">删除</button>
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
  name: 'RecurringTaskDetail',
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
    const taskInstances = ref([])
    
    // 获取任务详情
    const fetchTaskDetail = async () => {
      try {
        const taskId = route.params.id
        // 这里需要添加获取任务详情的API调用
        // 暂时使用假数据
        task.value = {
          id: taskId,
          title: '示例重复任务',
          description: '这是一个示例重复任务的详细描述',
          status: 'active',
          priority: 'medium',
          recurrence_type: 'weekly',
          recurrence_interval: 1,
          recurrence_rule: '1,3,5',
          recurrence_end_type: 'never',
          created_at: new Date()
        }
        
        // 获取任务实例
        taskInstances.value = [
          {
            id: 1,
            title: '示例任务实例 1',
            description: '这是第一个任务实例',
            status: 'completed',
            priority: 'medium',
            start_time: new Date(),
            end_time: new Date()
          },
          {
            id: 2,
            title: '示例任务实例 2',
            description: '这是第二个任务实例',
            status: 'in_progress',
            priority: 'medium',
            start_time: new Date(Date.now() + 86400000),
            end_time: new Date(Date.now() + 172800000)
          }
        ]
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
      if (confirm('确定要删除这个重复任务吗？')) {
        console.log('删除任务:', taskId)
        router.push('/tasks')
      }
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        not_started: '未开始',
        in_progress: '进行中',
        completed: '已完成',
        cancelled: '已取消',
        overdue: '已过期',
        active: '激活',
        inactive: 'inactive'
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
    
    // 获取重复文本
    const getRecurrenceText = (task) => {
      const typeMap = {
        daily: '每天',
        weekly: '每周',
        monthly: '每月',
        yearly: '每年'
      }
      let text = `${typeMap[task.recurrence_type]} 每 ${task.recurrence_interval} 天/周/月/年`
      if (task.recurrence_end_type === 'never') {
        text += '，永不结束'
      } else if (task.recurrence_end_type === 'on_date' && task.recurrence_end_date) {
        text += `，截止到 ${task.recurrence_end_date}`
      } else if (task.recurrence_end_type === 'after_occurrences' && task.recurrence_occurrences) {
        text += `，共 ${task.recurrence_occurrences} 次`
      }
      return text
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
      taskInstances,
      goBack,
      editTask,
      deleteTask,
      getStatusText,
      getPriorityText,
      getRecurrenceText,
      formatDate
    }
  }
}
</script>

<style scoped>
.recurring-task-detail-page {
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
  margin-bottom: 30px;
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
  min-width: 100px;
}

.task-instances-list {
  margin-top: 30px;
}

.task-instances-list h3 {
  font-size: 18px;
  margin-bottom: 15px;
  color: #333;
  font-weight: 600;
}

.instance-cards {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.instance-card {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #f0f0f0;
}

.instance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.instance-header h4 {
  margin: 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

.instance-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.instance-body p {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.4;
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
  background: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  color: #666;
  font-size: 14px;
}
</style>
