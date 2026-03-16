<template>
  <div class="task-detail-page">
    <!-- Toolbar -->
    <Toolbar :username="username" active="tasks" />
    
    <!-- Main Content -->
    <div class="main-content">
      <div class="detail-container">
        <!-- Left Side: Task Details -->
        <div class="task-details-section">
          <div class="section-header">
            <h2>{{ task.title }}</h2>
            <span class="task-type" :class="`task-type-${task.task_type}`">
              {{ getTaskTypeText(task.task_type) }}
            </span>
          </div>
          
          <div class="task-info">
            <div class="info-item">
              <label>描述</label>
              <p>{{ task.description }}</p>
            </div>
            <div class="info-item">
              <label>状态</label>
              <span class="status-badge" :class="`status-${task.status}`">
                {{ getStatusText(task.status) }}
              </span>
            </div>
            <div class="info-item">
              <label>创建时间</label>
              <p>{{ formatDate(task.created_at) }}</p>
            </div>
            <div class="info-item">
              <label>更新时间</label>
              <p>{{ formatDate(task.updated_at) }}</p>
            </div>
          </div>
          
          <!-- Repeat Task Specific Info -->
          <div class="task-specific-info">
            <h3>重复设置</h3>
            <div class="repeat-info">
              <div class="info-item">
                <label>重复频率</label>
                <p>{{ getRepeatFrequencyText(task.repeat_frequency) }}</p>
              </div>
              <div class="info-item">
                <label>开始日期</label>
                <p>{{ formatDate(task.start_date) }}</p>
              </div>
              <div class="info-item">
                <label>结束日期</label>
                <p>{{ task.end_date ? formatDate(task.end_date) : '无' }}</p>
              </div>
              <div class="info-item">
                <label>提醒时间</label>
                <p>{{ task.reminder_time || '无' }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Right Side: Chat Agent -->
        <div class="chat-section">
          <div class="chat-header">
            <h3>目标智能体</h3>
          </div>
          <div class="chat-container">
            <div class="chat-messages">
              <div 
                v-for="(message, index) in chatMessages" 
                :key="index"
                class="chat-message"
                :class="message.sender === 'user' ? 'user-message' : 'agent-message'"
              >
                <div class="message-content">
                  <p>{{ message.content }}</p>
                </div>
                <div class="message-time">{{ message.timestamp }}</div>
              </div>
            </div>
            <div class="chat-input-area">
              <input 
                type="text" 
                v-model="chatInput" 
                placeholder="输入消息..."
                class="chat-input"
                @keyup.enter="sendMessage"
              />
              <button @click="sendMessage" class="send-button">发送</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Toolbar from './Toolbar.vue';
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getTaskDetail, taskChat } from '../api/task';

export default {
  name: 'TaskDetailRepeat',
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
    const route = useRoute();
    const taskId = route.params.id;
    const task = ref({});
    const chatMessages = ref([]);
    const chatInput = ref('');
    
    // 加载任务详情
    const loadTaskDetail = async () => {
      try {
        const response = await getTaskDetail(taskId);
        task.value = response;
      } catch (error) {
        console.error('加载任务详情失败:', error);
      }
    };
    
    // 发送消息
    const sendMessage = async () => {
      if (!chatInput.value.trim()) return;
      
      // 添加用户消息
      chatMessages.value.push({
        sender: 'user',
        content: chatInput.value,
        timestamp: new Date().toLocaleTimeString()
      });
      
      try {
        const response = await taskChat({
          task_id: taskId,
          input: chatInput.value
        });
        // 添加智能体回复
        chatMessages.value.push({
          sender: 'agent',
          content: response,
          timestamp: new Date().toLocaleTimeString()
        });
      } catch (error) {
        console.error('发送消息失败:', error);
        // 添加错误消息
        chatMessages.value.push({
          sender: 'agent',
          content: '抱歉，智能体暂时无法响应，请稍后再试。',
          timestamp: new Date().toLocaleTimeString()
        });
      } finally {
        // 清空输入框
        chatInput.value = '';
      }
    };
    
    // 获取任务类型文本
    const getTaskTypeText = (type) => {
      const typeMap = {
        'once': '一次性',
        'repeat': '重复',
        'complex': '复杂'
      };
      return typeMap[type] || type;
    };
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'NOT_STARTED': '未开始',
        'IN_PROGRESS': '进行中',
        'COMPLETED': '已完成',
        'CANCELLED': '已取消'
      };
      return statusMap[status] || status;
    };
    
    // 获取重复频率文本
    const getRepeatFrequencyText = (frequency) => {
      const frequencyMap = {
        'daily': '每天',
        'weekly': '每周',
        'monthly': '每月',
        'yearly': '每年'
      };
      return frequencyMap[frequency] || frequency;
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    // 组件挂载时加载数据
    onMounted(() => {
      loadTaskDetail();
    });
    
    return {
      task,
      chatMessages,
      chatInput,
      sendMessage,
      getTaskTypeText,
      getStatusText,
      getRepeatFrequencyText,
      formatDate
    };
  }
};
</script>

<style scoped>
.task-detail-page {
  min-height: 100vh;
  background-color: var(--color-gray-light);
}

.main-content {
  padding: var(--spacing-lg);
  max-width: 1200px;
  margin: 0 auto;
}

.detail-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-lg);
}

.task-details-section {
  background-color: var(--color-white);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--box-shadow-sm);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-lg);
}

.section-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--color-gray-dark);
}

.task-type {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: bold;
}

.task-type-once {
  background-color: var(--color-task-light);
  color: var(--color-task);
}

.task-type-repeat {
  background-color: var(--color-recurring-light);
  color: var(--color-recurring);
}

.task-type-complex {
  background-color: var(--color-okr-light);
  color: var(--color-okr);
}

.task-info {
  margin-bottom: var(--spacing-lg);
}

.info-item {
  margin-bottom: var(--spacing-md);
}

.info-item label {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--color-gray-medium);
  margin-bottom: var(--spacing-xs);
}

.info-item p {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--color-gray-dark);
}

.status-badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: bold;
}

.status-NOT_STARTED {
  background-color: rgba(255, 193, 7, 0.1);
  color: var(--color-not-started);
}

.status-IN_PROGRESS {
  background-color: var(--color-task-light);
  color: var(--color-in-progress);
}

.status-COMPLETED {
  background-color: rgba(40, 167, 69, 0.1);
  color: var(--color-completed);
}

.status-CANCELLED {
  background-color: rgba(108, 117, 125, 0.1);
  color: var(--color-cancelled);
}

.task-specific-info {
  margin-top: var(--spacing-lg);
}

.task-specific-info h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: var(--font-size-lg);
  color: var(--color-gray-dark);
}

.repeat-info {
  background-color: var(--color-recurring-light);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md);
}

.chat-section {
  background-color: var(--color-white);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--box-shadow-sm);
  display: flex;
  flex-direction: column;
}

.chat-header {
  margin-bottom: var(--spacing-md);
}

.chat-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-gray-dark);
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--color-gray-light);
  border-radius: var(--border-radius-md);
}

.chat-message {
  margin-bottom: var(--spacing-md);
  max-width: 80%;
}

.user-message {
  align-self: flex-end;
  margin-left: auto;
}

.agent-message {
  align-self: flex-start;
}

.message-content {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-sm);
  line-height: 1.4;
}

.user-message .message-content {
  background-color: var(--color-task);
  color: var(--color-white);
}

.agent-message .message-content {
  background-color: var(--color-white);
  color: var(--color-gray-dark);
  border: 1px solid var(--color-task-border);
}

.message-time {
  font-size: var(--font-size-xs);
  color: var(--color-gray-medium);
  margin-top: var(--spacing-xs);
  text-align: right;
}

.chat-input-area {
  display: flex;
  gap: var(--spacing-sm);
}

.chat-input {
  flex: 1;
  padding: var(--spacing-md);
  border: 1px solid var(--color-task-border);
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-md);
}

.send-button {
  padding: 0 var(--spacing-lg);
  background-color: var(--color-task);
  color: var(--color-white);
  border: none;
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-md);
  cursor: pointer;
  transition: var(--transition-fast);
}

.send-button:hover {
  background-color: var(--color-task-hover);
}

@media (max-width: 768px) {
  .detail-container {
    grid-template-columns: 1fr;
  }
  
  .chat-section {
    margin-top: var(--spacing-lg);
  }
}
</style>