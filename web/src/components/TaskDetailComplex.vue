<template>
  <div class="task-detail-page">
    <!-- Toolbar -->
    <Toolbar :username="username" active="tasks" />
    
    <!-- Main Content -->
    <div class="main-content">
      <div class="detail-container" :class="{ 'expanded': isNavExpanded }">
        <!-- Left Side: Subtask Navigation -->
        <div class="subtask-nav-section" :class="{ 'expanded': isNavExpanded }">
          <div class="nav-header">
            <button class="toggle-button" @click="toggleNav">
              {{ isNavExpanded ? '«' : '»' }}
            </button>
          </div>
          <div class="subtask-tree" v-if="isNavExpanded">
            <!-- 渲染子任务树 -->
            <div v-if="subtaskTree" class="tree-root">
              <div class="tree-item root-item" :class="{ 'selected': selectedTaskId === subtaskTree.id }" @click="selectTask(subtaskTree)">
                <div class="tree-item-content">
                  <img v-if="selectedTaskId === subtaskTree.id" src="../assets/selected.png" alt="selected" class="selected-icon" />
                  <span class="task-title">{{ subtaskTree.name }}</span>
                </div>
              </div>
              <!-- 递归渲染子任务 -->
              <div v-if="subtaskTree.children && subtaskTree.children.length > 0" class="subtree-container">
                <template v-for="child in subtaskTree.children" :key="child.id">
                  <div class="subtask-item-container">
                    <div class="tree-item" :class="{ 'selected': selectedTaskId === child.id }" @click="selectTask(child)">
                      <div class="tree-item-content">
                        <img v-if="selectedTaskId === child.id" src="../assets/selected.png" alt="selected" class="selected-icon" />
                        <span class="task-title">{{ child.name }}</span>
                      </div>
                    </div>
                    <!-- 递归渲染子任务的子任务 -->
                    <div v-if="child.children && child.children.length > 0" class="subtree-container">
                      <template v-for="grandchild in child.children" :key="grandchild.id">
                        <div class="subtask-item-container">
                          <div class="tree-item" :class="{ 'selected': selectedTaskId === grandchild.id }" @click="selectTask(grandchild)">
                            <div class="tree-item-content">
                              <img v-if="selectedTaskId === grandchild.id" src="../assets/selected.png" alt="selected" class="selected-icon" />
                              <span class="task-title">{{ grandchild.name }}</span>
                            </div>
                          </div>
                          <!-- 可以继续递归渲染更深层次的子任务 -->
                          <div v-if="grandchild.children && grandchild.children.length > 0" class="subtree-container">
                            <template v-for="greatgrandchild in grandchild.children" :key="greatgrandchild.id">
                              <div class="subtask-item-container">
                                <div class="tree-item" :class="{ 'selected': selectedTaskId === greatgrandchild.id }" @click="selectTask(greatgrandchild)">
                                  <div class="tree-item-content">
                                    <img v-if="selectedTaskId === greatgrandchild.id" src="../assets/selected.png" alt="selected" class="selected-icon" />
                                    <span class="task-title">{{ greatgrandchild.name }}</span>
                                  </div>
                                </div>
                              </div>
                            </template>
                          </div>
                        </div>
                      </template>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Middle Side: Task Information -->
        <div class="task-info-section">
          <div class="section-header">
            <h2>{{ selectedTask.title || selectedTask.name || '任务详情' }}</h2>
            <span class="task-type" :class="`task-type-${selectedTask.task_type || 'once'}`">
              {{ getTaskTypeText(selectedTask.task_type || 'once') }}
            </span>
          </div>
          
          <div class="task-info">
            <div class="info-item">
              <label>描述</label>
              <p>{{ selectedTask.description || '暂无描述' }}</p>
            </div>
            <div class="info-item">
              <label>状态</label>
              <span class="status-badge" :class="`status-${selectedTask.status || 'NOT_STARTED'}`">
                {{ getStatusText(selectedTask.status || 'NOT_STARTED') }}
              </span>
            </div>
            <div class="info-item">
              <label>创建时间</label>
              <p>{{ formatDate(selectedTask.created_at) || '-' }}</p>
            </div>
            <div class="info-item">
              <label>更新时间</label>
              <p>{{ formatDate(selectedTask.updated_at) || '-' }}</p>
            </div>
          </div>
          
          <!-- Complex Task Specific Info -->
          <div v-if="selectedTask.task_type === 'complex'" class="task-specific-info">
            <h3>子目标列表</h3>
            <div class="subtasks-list">
              <div 
                v-for="subtask in selectedTask.subtasks || []" 
                :key="subtask.id" 
                class="subtask-item"
                @click="selectTask(subtask)"
              >
                <div class="subtask-header">
                  <h4>{{ subtask.title }}</h4>
                  <div class="subtask-meta">
                    <span class="subtask-type" :class="`task-type-${subtask.task_type}`">
                      {{ getTaskTypeText(subtask.task_type) }}
                    </span>
                    <span class="subtask-status" :class="`status-${subtask.status}`">
                      {{ getStatusText(subtask.status) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
      </div>
      <div class="chat-window">
          <div class="chat-header">
            <h3>⭐奶小豆⭐</h3>
          </div>
          <div class="messages" ref="messagesContainer">
            <div 
              v-for="(message, index) in chatMessages" 
              :key="index"
              class="message"
              :class="message.sender === 'user' ? 'user' : 'agent'"
            >
              <div class="message-avatar" v-if="message.sender === 'agent'">
                <span class="chat-bot-initial">🤖</span>
              </div>
              <div class="message-content">
                <div class="message-text" :class="{ 'is-loading': message.isTyping }">
                  <div v-if="message.isTyping" class="chat-typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <div v-else v-html="formatMessage(message.content)"></div>
                </div>
                <div class="message-time" v-if="!message.isTyping">{{ message.timestamp }}</div>
              </div>
              <div class="message-avatar" v-if="message.sender === 'user'">
                <span class="chat-user-initial">{{ userInitial }}</span>
              </div>
            </div>
          </div>
      </div>
    </div>
    
    <!-- Chat Input Area (Floating at bottom) -->
    <div class="message-section">
      <div class="message-area">
        <div class="message-container">
          <textarea 
          v-model="chatInput" 
          placeholder="输入消息..."
          class="message-input"
          @keydown.enter.exact="handleEnter"
          @keydown.enter.ctrl="handleCtrlEnter"
          @input="autoResize"
          ref="chatTextarea"
        ></textarea>
          <button @click="sendMessage" :disabled="!chatInput.trim() || sending" class="chat-send-btn">
            <span v-if="!sending">发送</span>
            <span v-else class="chat-loading-dot">●</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Toolbar from './Toolbar.vue';
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { getTaskDetail, getTaskSubtasks, getChatHistory } from '../api/task';
import { marked } from 'marked';

export default {
  name: 'TaskDetailComplex',
  components: {
    Toolbar
  },
  props: {
    username: {
      type: String,
      default: '用户'
    }
  },
  setup(props) {
    const route = useRoute();
    const taskId = route.params.id;
    const task = ref({});
    const subtaskTree = ref(null);
    const selectedTaskId = ref('');
    const isNavExpanded = ref(false);
    const chatMessages = ref([]);
    const chatInput = ref('');
    const messagesContainer = ref(null);
    const chatTextarea = ref(null);
    const taskMap = ref({});
    const sending = ref(false);
    
    // 计算当前选中的任务
    const selectedTask = computed(() => {
      return taskMap.value[selectedTaskId.value] || task.value;
    });
    
    // 计算用户首字母
    const userInitial = computed(() => {
      return props.username.charAt(0).toUpperCase();
    });
    
    // 构建任务映射，方便快速查找任务
    const buildTaskMap = (taskTree) => {
      if (!taskTree) return;
      
      taskMap.value[taskTree.id] = taskTree;
      
      if (taskTree.children && taskTree.children.length > 0) {
        taskTree.children.forEach(child => {
          buildTaskMap(child);
        });
      }
    };
    
    // 加载任务详情
    const loadTaskDetail = async () => {
      try {
        // 加载任务详情
        const taskResponse = await getTaskDetail(taskId);
        task.value = taskResponse;
        selectedTaskId.value = taskResponse.id;
        
        // 加载子任务树
        const subtreeResponse = await getTaskSubtasks(taskId);
        subtaskTree.value = subtreeResponse;
        
        // 构建任务映射
        buildTaskMap(subtreeResponse);
      } catch (error) {
        console.error('加载任务详情失败:', error);
      }
    };
    
    // 切换导航栏展开/折叠
    const toggleNav = () => {
      isNavExpanded.value = !isNavExpanded.value;
    };
    
    // 选择任务
    const selectTask = async (taskItem) => {
      console.log('选择任务:', taskItem);
      selectedTaskId.value = taskItem.id;
      
      // 每次点击都加载任务详情，确保数据是最新的
      try {
        const taskResponse = await getTaskDetail(taskItem.id);
        // 使用 Vue 的响应式更新方式
        taskMap.value = {
          ...taskMap.value,
          [taskItem.id]: taskResponse
        };
        console.log('任务详情加载成功:', taskResponse);
      } catch (error) {
        console.error('加载任务详情失败:', error);
      }
    };
    
    // 处理 Enter 键（提交消息）
    const handleEnter = (event) => {
      event.preventDefault();
      sendMessage();
    };
    
    // 处理 Ctrl+Enter 键（换行）
    const handleCtrlEnter = () => {
      // 允许默认行为（换行）
    };
    
    // 自动调整 textarea 高度
    const autoResize = () => {
      if (chatTextarea.value) {
        // 重置高度，以便正确计算 scrollHeight
        chatTextarea.value.style.height = 'auto';
        
        // 计算适合的高度，最大支持6行
        const lineHeight = 20; // 假设行高为20px
        const maxLines = 6;
        const maxHeight = lineHeight * maxLines;
        
        // 计算内容高度
        const contentHeight = chatTextarea.value.scrollHeight;
        
        // 设置高度，不超过最大高度
        chatTextarea.value.style.height = `${Math.min(contentHeight, maxHeight)}px`;
      }
    };
    
    // 格式化消息内容（解析 markdown）
    const formatMessage = (text) => {
      // 使用marked库解析markdown文本
      return marked.parse(text) || '';
    };
    
    // 滚动到底部
    const scrollToBottom = () => {
      setTimeout(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        }
      }, 100);
    };
    
    // 加载聊天历史
    const loadChatHistory = async () => {
      try {
        // 加载最近的聊天历史
        const response = await getChatHistory(1, 10);
        if (response && response.history && response.history.length > 0) {
          // 加载历史消息
          chatMessages.value = response.history.map(msg => ({
            sender: msg.sender || (msg.type === 'assistant' ? 'agent' : 'user'),
            content: msg.content,
            timestamp: new Date(msg.timestamp || Date.now()).toLocaleTimeString()
          }));
          scrollToBottom();
        }
      } catch (error) {
        console.error('加载聊天历史失败:', error);
        // 保持默认消息
      }
    };
    
    // 发送消息
    const sendMessage = async () => {
      if (!chatInput.value.trim() || sending.value) return;
      
      // 添加用户消息
      const userMessage = {
        sender: 'user',
        content: chatInput.value,
        timestamp: new Date().toLocaleTimeString()
      };
      chatMessages.value.push(userMessage);
      
      const userInput = chatInput.value;
      chatInput.value = '';
      autoResize();
      
      // 模拟发送消息
      sending.value = true;
      
      try {
        // 添加一个正在输入的提示
        const typingMessage = {
          sender: 'agent',
          isTyping: true,
          timestamp: new Date()
        };
        chatMessages.value.push(typingMessage);
        scrollToBottom();
        
        // 调用真实的API - 使用fetch处理流式响应
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000'}/api/tasks/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ 
            task_id: selectedTaskId.value,
            input: userInput 
          })
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 移除正在输入的提示
        chatMessages.value.pop();
        
        // 添加机器人回复消息（初始为空）
        const botResponse = {
          sender: 'agent',
          content: '',
          timestamp: new Date().toLocaleTimeString()
        };
        const botMessageIndex = chatMessages.value.push(botResponse) - 1;
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');  // 明确指定UTF-8编码
        let done = false;
        let buffer = '';  // 用于处理可能的分割字符
        
        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          
          if (value) {
            const chunk = decoder.decode(value, { stream: !done });  // 对于最后一个块，不使用stream模式
            // 将块添加到缓冲区
            buffer += chunk+'\n';
            
            // 按行分割处理（因为后端可能返回多行JSON）
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';  // 保留最后一个不完整的行在缓冲区中
            
            for (const line of lines) {
              if (line.trim()) {  // 忽略空行
                try {
                  const data = JSON.parse(line);
                  
                  // 只更新内容部分，忽略其他类型的消息
                  if (data.type === 'assistant' && data.content) {
                    chatMessages.value[botMessageIndex].content += data.content;
                    scrollToBottom();
                  } else if (data.type === 'start' || data.type === 'end') {
                    // 可以根据需要处理开始和结束消息
                    console.log('Stream event:', data.type, data.content);
                  }
                } catch (e) {
                  console.error('解析JSON失败:', e);
                  // 如果不是有效的JSON，直接添加到内容中
                  chatMessages.value[botMessageIndex].content += line;
                  scrollToBottom();
                }
              }
            }
          }
        }
        
        // 处理缓冲区中剩余的内容
        if (buffer) {
          try {
            const data = JSON.parse(buffer);
            if (data.type === 'assistant' && data.content) {
              chatMessages.value[botMessageIndex].content += data.content;
              scrollToBottom();
            }
          } catch (e) {
            // 如果不是有效的JSON，直接添加到内容中
            chatMessages.value[botMessageIndex].content += buffer;
            scrollToBottom();
          }
        }
      } catch (error) {
        console.error('发送消息失败:', error);
        // 移除正在输入的提示
        chatMessages.value.pop();
        // 添加错误消息
        chatMessages.value.push({
          sender: 'agent',
          content: '抱歉，智能体暂时无法响应，请稍后再试。',
          timestamp: new Date().toLocaleTimeString()
        });
        scrollToBottom();
      } finally {
        sending.value = false;
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
    onMounted(async () => {
      await loadTaskDetail();
      await loadChatHistory();
      // 滚动到底部
      scrollToBottom();
    });
    
    // 监听输入框变化，自动调整高度
    watch(chatInput, () => {
      autoResize();
    });
    
    return {
      task,
      subtaskTree,
      selectedTaskId,
      selectedTask,
      isNavExpanded,
      chatMessages,
      chatInput,
      messagesContainer,
      chatTextarea,
      userInitial,
      sending,
      toggleNav,
      selectTask,
      sendMessage,
      handleEnter,
      handleCtrlEnter,
      autoResize,
      formatMessage,
      loadChatHistory,
      getTaskTypeText,
      getStatusText,
      formatDate
    };
  }
};
</script>

<style scoped>
@import '../styles/chat-window.css';

.message-area {
  background : #ffffff00;
  border-top : none;
}

.task-detail-page {
  min-height: 98vh;
  background-color: var(--color-gray-light);
}

.main-content {
  padding: 4vh 0vh 0vh 0vh;
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  height: 93vh;
  justify-content: center;
}

.detail-container {
  display: flex;
  grid-template-columns: 4% 1fr 300px;
  gap: 0;
  transition: grid-template-columns 0.3s ease;
  width: 40%;
}

/* 展开状态下的布局 */
.detail-container.expanded {
  grid-template-columns: 10% 1fr 300px;
}

/* 左侧子任务导航 */
.subtask-nav-section {
  background-color: var(--color-white);
  border-radius: var(--border-radius-lg) 0 0 var(--border-radius-lg);
  padding: var(--spacing-md);
  box-shadow: var(--box-shadow-sm);
  transition: all 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 3%;
  height: 95%;
}

.subtask-nav-section.expanded {
  width: 20%;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--spacing-md);
}

.toggle-button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background-color: var(--color-task-light);
  color: var(--color-task);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  margin: 0 auto;
}

.toggle-button:hover {
  background-color: var(--color-task);
  color: var(--color-white);
}

.nav-header h3 {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--color-gray-dark);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtask-tree {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.tree-item {
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtree-container {
  
}

.subtask-item-container {
  margin-bottom: var(--spacing-xs);
}

.tree-item:hover {
  background-color: var(--color-gray-light);
}

.tree-item.selected {
  background-color: var(--color-task-light);
  border-left: 3px solid var(--color-task);
}

.root-item {
  font-weight: bold;
  margin-bottom: var(--spacing-md);
}

.tree-item-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.selected-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.task-title {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 中间任务信息 */
.task-info-section {
  background-color: var(--color-white);
  border-radius: 0 var(--border-radius-lg) var(--border-radius-lg) 0;
  padding: var(--spacing-md);
  box-shadow: var(--box-shadow-sm);
  width: auto;
  flex: 1;
  height: 95%;
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

.subtasks-list {
  margin-bottom: var(--spacing-lg);
}

.subtask-item {
  border: 1px solid var(--color-task-border);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  background-color: var(--color-task-light);
  cursor: pointer;
  transition: var(--transition-fast);
}

.subtask-item:hover {
  box-shadow: var(--box-shadow-md);
  transform: translateY(-2px);
}

.subtask-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.subtask-header h4 {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--color-gray-dark);
  flex: 1;
}

.subtask-meta {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.subtask-type {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: bold;
}

.subtask-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: bold;
}

/* 右侧AI对话 */
.chat-window {
  width: 45%;
  height: 90%;
}

/* 聊天输入区域 (悬浮在页面下方) */
.message-section {
  position: fixed;
  bottom: 20px;
  left: 50%; /* 将元素左侧定位到屏幕中心 */
  transform: translateX(-50%); /* 向左移动元素自身宽度的一半，实现水平居中 */
  width: 80%;
  background-color: transparent;
  border-radius: var(--border-radius-lg);
  box-shadow: none;
  z-index: 1000;
  border: none;
  padding: var(--spacing-ls);
}

.chat-send-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(45deg, #ff6b6b, #ffa500);
  color: white;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.chat-send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

.chat-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .detail-container {
    grid-template-columns: 1fr;
  }
  
  .subtask-nav-section {
    order: 1;
    grid-column: 1;
  }
  
  .task-info-section {
    order: 2;
    grid-column: 1;
  }
  
  .chat-window {
    order: 3;
    grid-column: 1;
    margin-top: var(--spacing-lg);
    width: 100%;
  }
  
  .subtask-nav-section.expanded {
    width: 100%;
  }
  
  .message-section {
    width: 95%;
    bottom: 10px;
  }
}
</style>