<template>
  <div class="okr-detail-page">
    <!-- 工具栏 -->
    <Toolbar :username="username" />
    
    <!-- 页面内容 -->
    <div class="page-content">
      <div class="page-header">
        <h1>OKR详情</h1>
        <button @click="goBack" class="btn-secondary">返回</button>
      </div>
      
      <div v-if="okr" class="okr-detail-card">
        <div class="card-header" :class="okr.status">
          <h2>{{ okr.objective }}</h2>
          <div class="priority-indicator medium">
            <span class="priority-text">中</span>
          </div>
        </div>
        <div class="card-body">
          <p v-if="okr.description" class="okr-description">{{ okr.description }}</p>
          <div class="okr-meta">
            <div class="meta-item">
              <span class="meta-label">状态：</span>
              <span :class="['status-badge', okr.status]">{{ getStatusText(okr.status) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">时间范围：</span>
              <span class="time-badge">{{ formatShortDate(okr.start_date) }} - {{ formatShortDate(okr.end_date) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建时间：</span>
              <span>{{ formatDate(okr.created_at) }}</span>
            </div>
          </div>
          
          <!-- 关键结果列表 -->
          <div class="kr-list">
            <h3>关键结果 ({{ krs.length }})</h3>
            <div v-if="krs.length === 0" class="empty-state">
              暂无关键结果
            </div>
            <div v-else class="kr-cards">
              <div v-for="kr in krs" :key="kr.id" class="kr-card">
                <div class="kr-header">
                  <h4>{{ kr.title }}</h4>
                  <span :class="['status-badge', kr.status]">{{ getStatusText(kr.status) }}</span>
                </div>
                <div class="kr-body">
                  <p v-if="kr.description">{{ kr.description }}</p>
                  <div class="kr-progress" v-if="kr.target_value">
                    <span>{{ kr.current_value }} / {{ kr.target_value }} ({{ Math.round((kr.current_value / kr.target_value) * 100) }}%)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="card-footer">
          <button @click="editOKR(okr)" class="btn-complete">编辑</button>
          <button @click="deleteOKR(okr.id)" class="btn-cancel">删除</button>
          <button @click="showCreateKRDialog(okr.id)" class="btn-complete">添加KR</button>
        </div>
      </div>
      <div v-else class="empty-state">
        OKR不存在或已被删除
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
  name: 'OKRDetail',
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
    const okr = ref(null)
    const krs = ref([])
    
    // 获取OKR详情
    const fetchOKRDetail = async () => {
      try {
        const okrId = route.params.id
        // 这里需要添加获取OKR详情的API调用
        // 暂时使用假数据
        okr.value = {
          id: okrId,
          objective: '示例OKR目标',
          description: '这是一个示例OKR的详细描述',
          status: 'active',
          start_date: new Date(),
          end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
          created_at: new Date()
        }
        
        // 获取关键结果
        krs.value = [
          {
            id: 1,
            title: '示例关键结果 1',
            description: '这是第一个关键结果',
            status: 'in_progress',
            target_value: 100,
            current_value: 50
          },
          {
            id: 2,
            title: '示例关键结果 2',
            description: '这是第二个关键结果',
            status: 'completed',
            target_value: 80,
            current_value: 80
          }
        ]
      } catch (error) {
        console.error('获取OKR详情失败:', error)
      }
    }
    
    // 返回上一页
    const goBack = () => {
      router.push('/tasks')
    }
    
    // 编辑OKR
    const editOKR = (okr) => {
      console.log('编辑OKR:', okr)
    }
    
    // 删除OKR
    const deleteOKR = (okrId) => {
      if (confirm('确定要删除这个OKR吗？')) {
        console.log('删除OKR:', okrId)
        router.push('/tasks')
      }
    }
    
    // 显示创建KR对话框
    const showCreateKRDialog = (okrId) => {
      console.log('显示创建KR对话框:', okrId)
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
        inactive: 'inactive',
        draft: '草稿'
      }
      return statusMap[status] || status
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    // 格式化短日期（月/日）
    const formatShortDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit'
      })
    }
    
    // 组件挂载时获取OKR详情
    onMounted(async () => {
      await fetchOKRDetail()
    })
    
    return {
      okr,
      krs,
      goBack,
      editOKR,
      deleteOKR,
      showCreateKRDialog,
      getStatusText,
      formatDate,
      formatShortDate
    }
  }
}
</script>

<style scoped>
.okr-detail-page {
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

.okr-detail-card {
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

.okr-description {
  font-size: 16px;
  line-height: 1.5;
  color: #666;
  margin-bottom: 20px;
}

.okr-meta {
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

.kr-list {
  margin-top: 30px;
}

.kr-list h3 {
  font-size: 18px;
  margin-bottom: 15px;
  color: #333;
  font-weight: 600;
}

.kr-cards {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.kr-card {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #f0f0f0;
}

.kr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.kr-header h4 {
  margin: 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
  flex: 1;
}

.kr-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kr-body p {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.4;
}

.kr-progress {
  font-size: 14px;
  color: #4a90e2;
  font-weight: 500;
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
