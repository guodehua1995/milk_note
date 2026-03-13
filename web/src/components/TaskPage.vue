<template>
  <div class="task-page">
    <!-- Toolbar -->
    <Toolbar :username="username" active="tasks" />
    
    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Side: Search and Stats -->
      <div class="left-section">
        <div class="search-stats-section">
          <div class="search-bar">
            <input 
              type="text" 
              v-model="searchTitle" 
              placeholder="搜索目标标题"
              class="search-input"
            />
            <select v-model="searchType" class="search-select">
              <option value="">所有类型</option>
              <option value="once">一次性目标</option>
              <option value="repeat">重复目标</option>
              <option value="complex">复杂目标</option>
            </select>
            <button class="search-button" @click="searchTasks">搜索</button>
          </div>
          
          <!-- 新建任务按钮 -->
          <div class="create-task-section">
            <button class="create-task-button" @click="showTaskTypeModal = true">
              <i class="create-icon">+</i> 新建任务
            </button>
          </div>
          
          <!-- 统计数据 -->
          <div class="stats-container">
            <div class="stat-item">
              <span class="stat-label" style="color: var(--color-task)">目标总数</span>
              <span class="stat-value">{{ stats.total }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label" style="color: var(--color-not-started)">未开始</span>
              <span class="stat-value">{{ stats.notStarted }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label" style="color: var(--color-in-progress)">进行中</span>
              <span class="stat-value">{{ stats.inProgress }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label" style="color: var(--color-completed)">已完成</span>
              <span class="stat-value">{{ stats.completed }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label" style="color: var(--color-cancelled)">已取消</span>
              <span class="stat-value">{{ stats.cancelled }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 任务类型选择模态框 -->
      <div v-if="showTaskTypeModal" class="modal-overlay" @click="showTaskTypeModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>选择任务类型</h3>
            <button class="close-button" @click="showTaskTypeModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="task-type-options">
              <div 
                class="task-type-option" 
                @click="createTask('once')"
              >
                <div class="option-icon once-icon">📋</div>
                <div class="option-content">
                  <h4>一次性目标</h4>
                  <p>完成一次即可的任务</p>
                </div>
              </div>
              <div 
                class="task-type-option" 
                @click="createTask('repeat')"
              >
                <div class="option-icon repeat-icon">🔄</div>
                <div class="option-content">
                  <h4>重复目标</h4>
                  <p>需要定期重复的任务</p>
                </div>
              </div>
              <div 
                class="task-type-option" 
                @click="createTask('complex')"
              >
                <div class="option-icon complex-icon">📊</div>
                <div class="option-content">
                  <h4>复杂目标</h4>
                  <p>包含多个子任务的复杂目标</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Right Side: Task List -->
      <div class="right-section">
        <div class="task-list-section">
          <div class="task-cards">
            <div 
              v-for="task in tasks" 
              :key="task.id" 
              class="task-card"
              @click="navigateToDetail(task)"
            >
              <div class="task-header">
                <h3 class="task-title">{{ task.title }}</h3>
                <span class="task-type" :class="`task-type-${task.task_type}`">
                  {{ getTaskTypeText(task.task_type) }}
                </span>
              </div>
              <p class="task-description">{{ task.description }}</p>
              <div class="task-footer">
                <span class="task-status" :class="`status-${task.status}`">
                  {{ getStatusText(task.status) }}
                </span>
                <div class="task-dates">
                  <span class="task-date">创建: {{ formatDate(task.created_at) }}</span>
                  <span class="task-date">更新: {{ formatDate(task.updated_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Empty State -->
          <div v-if="tasks.length === 0" class="empty-state">
            <p>暂无目标，请创建新目标</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Toolbar from './Toolbar.vue';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getTasks } from '../api/task';

export default {
  name: 'TaskPage',
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
    const router = useRouter();
    const tasks = ref([]);
    const searchTitle = ref('');
    const searchType = ref('');
    const stats = ref({
      total: 0,
      notStarted: 0,
      inProgress: 0,
      completed: 0,
      cancelled: 0
    });
    const showTaskTypeModal = ref(false);
    
    // 加载任务列表
    const loadTasks = async () => {
      try {
        const response = await getTasks();
        tasks.value = response.items;
        calculateStats();
      } catch (error) {
        console.error('加载任务失败:', error);
      }
    };
    
    // 搜索任务
    const searchTasks = async () => {
      try {
        // 这里可以根据搜索条件过滤任务
        // 目前后端API没有提供搜索参数，所以在前端过滤
        const response = await getTasks();
        let filteredTasks = response.items;
        
        if (searchTitle.value) {
          filteredTasks = filteredTasks.filter(task => 
            task.title.toLowerCase().includes(searchTitle.value.toLowerCase())
          );
        }
        
        if (searchType.value) {
          filteredTasks = filteredTasks.filter(task => 
            task.task_type === searchType.value
          );
        }
        
        tasks.value = filteredTasks;
        calculateStats();
      } catch (error) {
        console.error('搜索任务失败:', error);
      }
    };
    
    // 计算统计信息
    const calculateStats = () => {
      stats.value = {
        total: tasks.value.length,
        notStarted: tasks.value.filter(task => task.status === 'NOT_STARTED').length,
        inProgress: tasks.value.filter(task => task.status === 'IN_PROGRESS').length,
        completed: tasks.value.filter(task => task.status === 'COMPLETED').length,
        cancelled: tasks.value.filter(task => task.status === 'CANCELLED').length
      };
    };
    
    // 导航到详情页
    const navigateToDetail = (task) => {
      console.log('点击了任务卡片:', task);
      console.log('任务类型:', task.task_type);
      console.log('任务ID:', task.id);
      console.log('router对象:', router);
      if (task.type === 'once') {
        console.log('跳转到一次性任务详情页:', `/task-detail/${task.id}`);
        router.push(`/task-detail/${task.id}`);
      } else if (task.type === 'repeat') {
        console.log('跳转到重复任务详情页:', `/recurring-task-detail/${task.id}`);
        router.push(`/recurring-task-detail/${task.id}`);
      } else if (task.type === 'complex') {
        console.log('跳转到复杂任务详情页:', `/okr-detail/${task.id}`);
        router.push(`/okr-detail/${task.id}`);
      } else {
        console.log('未知任务类型:', task.type);
      }
    };
    
    // 新建任务
    const createTask = (taskType) => {
      showTaskTypeModal.value = false;
      // 跳转到对应的详情页，携带任务类型参数
      if (taskType === 'once') {
        router.push(`/task-detail/new?type=${taskType}`);
      } else if (taskType === 'repeat') {
        router.push(`/recurring-task-detail/new?type=${taskType}`);
      } else if (taskType === 'complex') {
        router.push(`/okr-detail/new?type=${taskType}`);
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
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    // 组件挂载时加载任务
    onMounted(() => {
      loadTasks();
    });
    
    return {
      tasks,
      searchTitle,
      searchType,
      stats,
      showTaskTypeModal,
      searchTasks,
      navigateToDetail,
      createTask,
      getTaskTypeText,
      getStatusText,
      formatDate
    };
  }
};
</script>

<style scoped>
.task-page {
  height: 93vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
  padding-top: 5vh;
  overflow: hidden;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  max-width: 90%;
  margin: 0 auto;
  height: calc(100vh - 5vh - var(--spacing-lg) * 2);
  overflow: hidden;
}

/* 大屏幕优化 */
@media (min-width: 1400px) {
  .main-content {
    max-width: 1400px;
  }
}

@media (min-width: 1800px) {
  .main-content {
    max-width: 1600px;
  }
  
  .task-cards {
    gap: var(--spacing-lg);
  }
  
  .task-card {
    padding: var(--spacing-lg);
  }
  
  .task-title {
    font-size: var(--font-size-lg);
  }
  
  .task-description {
    font-size: var(--font-size-md);
    max-height: 80px;
  }
}

.left-section {
  /* 左侧搜索和统计区域 */
}

.right-section {
  /* 右侧任务卡片区域 */
}

.search-stats-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--box-shadow-sm);
  border: 1px solid rgba(74, 144, 226, 0.1);
  min-height: 90%;
  height: fit-content;
  position: sticky;
}

.search-bar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.search-input {
  padding: var(--spacing-md);
  border: 2px solid var(--color-task-border);
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-md);
  background-color: var(--color-white);
  transition: var(--transition-fast);
}

/* 新建任务按钮 */
.create-task-section {
  margin-bottom: var(--spacing-lg);
}

.create-task-button {
  width: 100%;
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
  color: var(--color-white);
  border: none;
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-md);
  cursor: pointer;
  transition: var(--transition-fast);
  font-weight: 500;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

.create-task-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.create-icon {
  font-size: var(--font-size-lg);
  font-weight: bold;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-task);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2);
}

.search-select {
  width: 100%;
  padding: var(--spacing-md);
  border: 2px solid var(--color-task-border);
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-md);
  background-color: var(--color-white);
  transition: var(--transition-fast);
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%234a90e2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1em;
  padding-right: 2.5em;
}

.search-select:focus {
  outline: none;
  border-color: var(--color-task);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2);
}

.search-button {
  width: 100%;
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(135deg, var(--color-task) 0%, var(--color-task-hover) 100%);
  color: var(--color-white);
  border: none;
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-md);
  cursor: pointer;
  transition: var(--transition-fast);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.search-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-sm);
  background: linear-gradient(135deg, var(--color-task-light) 0%, rgba(255, 255, 255, 0.8) 100%);
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-task-border);
  transition: var(--transition-fast);
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--box-shadow-md);
}

.stat-label {
  display: block;
  font-size: var(--font-size-xs);
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.stat-value {
  display: block;
  font-size: var(--font-size-md);
  font-weight: bold;
  text-shadow: 0 1px 2px rgba(74, 144, 226, 0.2);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--color-white);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--box-shadow-lg);
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-task-border);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-gray-dark);
}

.close-button {
  background: none;
  border: none;
  font-size: var(--font-size-xl);
  color: var(--color-gray-medium);
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  transition: var(--transition-fast);
}

.close-button:hover {
  background-color: var(--color-task-light);
  color: var(--color-task);
}

.modal-body {
  /* 模态框内容 */
}

.task-type-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.task-type-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 2px solid var(--color-task-border);
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: var(--transition-fast);
  background: linear-gradient(135deg, var(--color-white) 0%, #f8fafd 100%);
}

.task-type-option:hover {
  border-color: var(--color-task);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
  transform: translateY(-2px);
}

.option-icon {
  font-size: var(--font-size-xl);
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-md);
  background-color: var(--color-task-light);
}

.once-icon {
  background-color: var(--color-task-light);
}

.repeat-icon {
  background-color: var(--color-recurring-light);
}

.complex-icon {
  background-color: var(--color-okr-light);
}

.option-content {
  flex: 1;
}

.option-content h4 {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: var(--font-size-md);
  color: var(--color-gray-dark);
}

.option-content p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-gray-medium);
}

.task-list-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--box-shadow-sm);
  border: 1px solid rgba(74, 144, 226, 0.1);
  min-height: 90%;
}

.task-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.task-card {
  border: 2px solid var(--color-task-border);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: var(--transition-fast);
  background: linear-gradient(135deg, var(--color-white) 0%, #f8fafd 100%);
  box-shadow: var(--box-shadow-sm);
  position: relative;
  overflow: hidden;
  width: 30%;
  height: 30%;
}

.task-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-task), var(--color-recurring));
  opacity: 0.8;
}

.task-card:hover {
  border-color: var(--color-task);
  box-shadow: 0 8px 24px rgba(74, 144, 226, 0.2);
  transform: translateY(-3px);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-sm);
}

.task-title {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-gray-dark);
  flex: 1;
  line-height: 1.4;
}

.task-type {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.task-type-once {
  background: linear-gradient(135deg, var(--color-task-light) 0%, rgba(74, 144, 226, 0.2) 100%);
  color: var(--color-task);
  border: 1px solid var(--color-task-border);
}

.task-type-repeat {
  background: linear-gradient(135deg, var(--color-recurring-light) 0%, rgba(63, 173, 225, 0.2) 100%);
  color: var(--color-recurring);
  border: 1px solid var(--color-recurring-border);
}

.task-type-complex {
  background: linear-gradient(135deg, var(--color-okr-light) 0%, rgba(76, 175, 80, 0.2) 100%);
  color: var(--color-okr);
  border: 1px solid var(--color-okr-border);
}

.task-description {
  margin: var(--spacing-sm) 0;
  font-size: var(--font-size-sm);
  color: var(--color-gray-medium);
  line-height: 1.5;
  max-height: 60px;
  overflow: hidden;
  position: relative;
}

.task-description::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 20px;
  background: linear-gradient(transparent, rgba(255, 255, 255, 0.9));
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: var(--spacing-md);
}

.task-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-NOT_STARTED {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 193, 7, 0.2) 100%);
  color: var(--color-not-started);
  border: 1px solid rgba(255, 193, 7, 0.3);
}

.status-IN_PROGRESS {
  background: linear-gradient(135deg, var(--color-task-light) 0%, rgba(74, 144, 226, 0.2) 100%);
  color: var(--color-in-progress);
  border: 1px solid var(--color-task-border);
}

.status-COMPLETED {
  background: linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, rgba(40, 167, 69, 0.2) 100%);
  color: var(--color-completed);
  border: 1px solid rgba(40, 167, 69, 0.3);
}

.status-CANCELLED {
  background: linear-gradient(135deg, rgba(108, 117, 125, 0.1) 0%, rgba(108, 117, 125, 0.2) 100%);
  color: var(--color-cancelled);
  border: 1px solid rgba(108, 117, 125, 0.3);
}

.task-dates {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--spacing-xs);
}

.task-date {
  font-size: var(--font-size-xs);
  color: var(--color-gray-medium);
  font-style: italic;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-gray-medium);
  font-size: var(--font-size-md);
  background: linear-gradient(135deg, var(--color-task-light) 0%, rgba(255, 255, 255, 0.8) 100%);
  border-radius: var(--border-radius-md);
  border: 1px dashed var(--color-task-border);
}

@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .search-stats-section {
    position: static;
    height: 100%;
  }
  
  .task-cards {
    grid-template-columns: 1fr;
  }
}
</style>