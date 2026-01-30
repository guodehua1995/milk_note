<template>
  <div class="task-page">
    <!-- 工具栏 -->
    <Toolbar :username="username" />
    
    <!-- 页面内容 -->
    <div class="page-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1>任务管理</h1>
          <!-- 任务状态图例 -->
          <div class="">
            
            <div class="legend-items">
              <div class="legend-title">
              <span>状态</span>  
              </div>
              <div class="legend-item">
                <div class="legend-color not_started"></div>
                <span>未开始</span>
              </div>
              <div class="legend-item">
                <div class="legend-color in_progress"></div>
                <span>进行中</span>
              </div>
              <div class="legend-item">
                <div class="legend-color completed"></div>
                <span>已完成</span>
              </div>
              <div class="legend-item">
                <div class="legend-color cancelled"></div>
                <span>已取消</span>
              </div>
              <div class="legend-item">
                <div class="legend-color overdue"></div>
                <span>已过期</span>
              </div>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button @click="showCreateTaskDialog = true" class="btn-primary">
            创建任务
          </button>
        </div>
      </div>

      <!-- 任务搜索条件 -->
      <div class="task-filters">
        <div class="filter-item">
          <label>任务类型</label>
          <select v-model="taskTypeFilter" class="filter-select">
            <option value="all">全部</option>
            <option value="once">一次性任务</option>
            <option value="recurring">重复任务</option>
            <option value="okrs">OKR</option>
          </select>
        </div>
        <div class="filter-item">
          <label>状态</label>
          <select v-model="taskStatusFilter" class="filter-select">
            <option value="all">全部</option>
            <option value="not_started">未开始</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
            <option value="overdue">已过期</option>
          </select>
        </div>
        <div class="filter-item">
          <label>优先级</label>
          <select v-model="taskPriorityFilter" class="filter-select">
            <option value="all">全部</option>
            <option value="low">低</option>
            <option value="medium">中</option>
            <option value="high">高</option>
          </select>
        </div>
        <div class="filter-item">
          <button @click="fetchAllData" class="btn-search">搜索</button>
        </div>
      </div>

      <!-- 任务列表 -->
      <div class="task-content">
        
        <!-- 所有任务卡片列表 -->
        <div class="task-cards">
          <!-- 一次性任务卡片 -->
          <div v-for="task in filteredTasks" :key="'task-' + task.id" class="task-card task-type-normal" :class="task.status" @click="goToTaskDetail(task.id)">
            <div class="card-header">
              <div class="card-title-container">
                <h3 class="task-title">{{ task.title }}</h3>
                <div :class="['priority-indicator', task.priority]">
                  <span class="priority-text">{{ getPriorityText(task.priority) }}</span>
                </div>
              </div>
            </div>
            <div class="card-body">
              <p v-if="task.description" class="task-description">{{ task.description }}</p>
              <div class="card-footer-content">
                <div class="card-time">
                  <span v-if="task.start_time && task.end_time" class="time-badge">{{ formatShortDate(task.start_time) }} - {{ formatShortDate(task.end_time) }}</span>
                  <span v-else-if="task.start_time" class="time-badge">{{ formatShortDate(task.start_time) }}</span>
                  <span v-else-if="task.end_time" class="time-badge">{{ formatShortDate(task.end_time) }}</span>
                </div>
                <div class="card-actions">
                  <button @click.stop="editTask(task)" class="btn-complete">完成</button>
                  <button @click.stop="deleteTask(task.id)" class="btn-cancel">取消</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 重复任务卡片 -->
          <div v-for="task in filteredRecurringTasks" :key="'recurring-' + task.id" class="task-card task-type-recurring" :class="task.status" @click="goToRecurringTaskDetail(task.id)">
            <div class="card-header">
              <div class="card-title-container">
                <h3>{{ task.title }}</h3>
                <div :class="['priority-indicator', task.priority]">
                  <span class="priority-text">{{ getPriorityText(task.priority) }}</span>
                </div>
              </div>
              <button 
                class="expand-btn"
                @click.stop="toggleTaskInstances(task.id)"
              >
                {{ expandedTaskInstances.includes(task.id) ? '▼' : '▶' }}
              </button>
            </div>
            <div class="card-body">
              <p v-if="task.description">{{ task.description }}</p>
              <div class="card-meta">
                <span class="recurrence-badge">{{ getRecurrenceText(task) }}</span>
              </div>
              
              <!-- 任务实例列表 -->
              <div v-if="expandedTaskInstances.includes(task.id)" class="task-instances-list">
                <h4>任务实例</h4>
                <div class="instance-cards">
                  <div v-if="getTaskInstancesByRecurringTask(task.id).length === 0" class="empty-state small">
                    暂无任务实例
                  </div>
                  <div v-else v-for="instance in getTaskInstancesByRecurringTask(task.id)" :key="'instance-' + instance.id" class="instance-card">
                    <div class="instance-header">
                      <h5>{{ instance.title }}</h5>
                      <button @click.stop="editTaskInstance(instance)" class="btn-sm">编辑</button>
                    </div>
                    <div class="instance-body">
                      <div class="instance-time">
                        <span v-if="instance.start_time" class="time-badge">{{ formatDate(instance.start_time) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-footer-content">
                <div class="card-time">
                  <!-- 时间显示 -->
                </div>
                <div class="card-actions">
                  <button @click.stop="editRecurringTask(task)" class="btn-complete">完成</button>
                  <button @click.stop="deleteTask(task.id)" class="btn-cancel">取消</button>
                </div>
              </div>
            </div>
          </div>

          <!-- OKR卡片 -->
          <div v-for="okr in filteredOKRs" :key="'okr-' + okr.id" class="task-card task-type-okr" :class="okr.status" @click="goToOKRDetail(okr.id)">
            <div class="card-header">
              <div class="card-title-container">
                <h3 class="task-title">{{ okr.objective }}</h3>
                <div class="priority-indicator medium">
                  <span class="priority-text">中</span>
                </div>
              </div>
            </div>
            <div class="card-body">
              <p v-if="okr.description" class="task-description">{{ okr.description }}</p>
              
              <!-- KR列表 -->
              <div class="kr-list">
                <h4>关键结果 ({{ getKRsByOKR(okr.id).length }}) | 待办任务 ({{ getTodoCountByOKR() }})</h4>
                <div v-for="kr in getKRsByOKR(okr.id)" :key="'kr-' + kr.id" class="kr-card">
                  <div class="kr-header">
                    <h5>{{ kr.title }}</h5>
                    <div class="kr-actions">
                      <button @click.stop="editKR(kr)" class="btn-sm">编辑</button>
                      <button @click.stop="deleteKR(kr.id)" class="btn-sm btn-danger">删除</button>
                    </div>
                  </div>
                  <div class="kr-body">
                    <p v-if="kr.description">{{ kr.description }}</p>
                    <div class="kr-meta">
                      <span class="kr-progress" v-if="kr.target_value">
                        {{ kr.current_value }} / {{ kr.target_value }} ({{ Math.round((kr.current_value / kr.target_value) * 100) }}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-footer-content">
                <div class="card-time">
                  <span class="time-badge">{{ formatShortDate(okr.start_date) }} - {{ formatShortDate(okr.end_date) }}</span>
                </div>
                <div class="card-actions">
                  <button @click.stop="showCreateKRDialog(okr.id)" class="btn-complete">添加KR</button>
                  <button @click.stop="editOKR(okr)" class="btn-complete">编辑</button>
                  <button @click.stop="deleteOKR(okr.id)" class="btn-cancel">删除</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredTasks.length === 0 && filteredRecurringTasks.length === 0 && filteredOKRs.length === 0" class="empty-state">
          暂无任务
        </div>
      </div>
    </div>

    <!-- 创建任务对话框 -->
    <div v-if="showCreateTaskDialog" class="dialog-overlay" @click="showCreateTaskDialog = false">
      <div class="dialog" @click.stop>
        <div class="dialog-header task">
          <h3>创建任务</h3>
          <button @click="showCreateTaskDialog = false" class="dialog-close">×</button>
        </div>
        <div class="dialog-content">
          <form @submit.prevent="handleCreateTask">
            <div class="form-group">
              <label>标题</label>
              <input v-model="newTask.title" type="text" required class="form-input">
            </div>
            <div class="form-group">
              <label>描述</label>
              <textarea v-model="newTask.description" class="form-textarea"></textarea>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>任务类型</label>
                <select v-model="newTask.type" class="form-select">
                  <option value="once">一次性任务</option>
                  <option value="recurring">重复任务</option>
                  <option value="okr">OKR</option>
                </select>
              </div>
              <div class="form-group">
                <label>优先级</label>
                <select v-model="newTask.priority" class="form-select">
                  <option value="low">低</option>
                  <option value="medium">中</option>
                  <option value="high">高</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>状态</label>
                <select v-model="newTask.status" class="form-select">
                  <option value="not_started">未开始</option>
                  <option value="in_progress">进行中</option>
                  <option value="completed">已完成</option>
                </select>
              </div>
              <div class="form-group">
                <CustomDateTimePicker v-model="newTask.start_time" label="开始时间" />
              </div>
              <div class="form-group">
                <CustomDateTimePicker v-model="newTask.end_time" label="结束时间" />
              </div>
            </div>
            
            <!-- 重复任务相关字段 -->
            <div v-if="newTask.type === 'recurring'" class="recurring-task-fields">
              <div class="form-row">
                <div class="form-group">
                  <label>重复类型</label>
                  <select v-model="newRecurringTask.recurrence_type" class="form-select" @change="updateRecurrenceRulePlaceholder">
                    <option value="daily">每天</option>
                    <option value="weekly">每周</option>
                    <option value="monthly">每月</option>
                    <option value="yearly">每年</option>
                  </select>
                </div>
              </div>
              <div class="form-group">
                <label>重复规则</label>
                <!-- 每天重复，不需要规则 -->
                <div v-if="newRecurringTask.recurrence_type === 'daily'" class="rule-description">
                  每天重复，无需设置具体规则
                </div>
                
                <!-- 每周重复，显示星期选择器 -->
                <div v-else-if="newRecurringTask.recurrence_type === 'weekly'" class="weekday-selector">
                  <button 
                    v-for="day in weekdays" 
                    :key="day.value"
                    :class="['weekday-btn', { selected: selectedWeekdays.includes(day.value) }]"
                    @click="toggleWeekday(day.value)"
                  >
                    {{ day.label }}
                  </button>
                </div>
                
                <!-- 每月重复，显示日期选择器 -->
                <div v-else-if="newRecurringTask.recurrence_type === 'monthly'" class="calendar-selector">
                  <div class="calendar-grid">
                    <div v-for="day in 31" :key="day"
                         :class="['calendar-day', { selected: selectedMonthDays.includes(day) }]"
                         @click="toggleMonthDay(day)">
                      {{ day }}
                    </div>
                  </div>
                </div>
                
                <!-- 每年重复，显示日期选择器 -->
                <div v-else-if="newRecurringTask.recurrence_type === 'yearly'" class="calendar-selector">
                  <div class="month-selector">
                    <label>月份</label>
                    <div class="month-buttons">
                      <button 
                        v-for="month in months" 
                        :key="month.value"
                        :class="['month-btn', { selected: selectedMonth === month.value }]"
                        @click="selectMonth(month.value)"
                      >
                        {{ month.label }}
                      </button>
                    </div>
                  </div>
                  <div class="day-selector">
                    <label>日期</label>
                    <div class="calendar-grid">
                      <div v-for="day in getDaysInMonth(selectedMonth)" :key="day"
                           :class="['calendar-day', { selected: selectedYearDays.includes(day) }]"
                           @click="toggleYearDay(day)">
                        {{ day }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 隐藏的输入字段，用于存储规则 -->
                <input v-model="newRecurringTask.recurrence_rule" type="hidden" required>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>重复结束类型</label>
                  <select v-model="newRecurringTask.recurrence_end_type" class="form-select">
                    <option value="never">永不结束</option>
                    <option value="on_date">指定日期</option>
                    <option value="after_occurrences">指定次数</option>
                  </select>
                </div>
                <div v-if="newRecurringTask.recurrence_end_type === 'on_date'" class="form-group">
                  <CustomDatePicker v-model="newRecurringTask.recurrence_end_date" label="结束日期" />
                </div>
                <div v-else-if="newRecurringTask.recurrence_end_type === 'after_occurrences'" class="form-group">
                  <label>结束次数</label>
                  <input v-model="newRecurringTask.recurrence_occurrences" type="number" min="1" class="form-input">
                </div>
              </div>
            </div>
            
            <!-- OKR相关字段 -->
            <div v-if="newTask.type === 'okr'" class="okr-fields">
              <div class="form-row">
                <div class="form-group">
                  <CustomDatePicker v-model="newOKR.start_date" label="开始日期" required />
                </div>
                <div class="form-group">
                  <CustomDatePicker v-model="newOKR.end_date" label="结束日期" required />
                </div>
              </div>
              <div class="form-group">
                <label>OKR状态</label>
                <select v-model="newOKR.status" class="form-select">
                  <option value="draft">草稿</option>
                  <option value="active">激活</option>
                  <option value="completed">已完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </div>
            </div>
            
            <div class="dialog-footer">
              <button type="button" @click="showCreateTaskDialog = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">创建</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 创建KR对话框 -->
    <div v-if="showCreateKRDialogFlag" class="dialog-overlay" @click="showCreateKRDialogFlag = false">
      <div class="dialog" @click.stop>
        <div class="dialog-header">
          <h3>创建KR</h3>
          <button @click="showCreateKRDialogFlag = false" class="dialog-close">×</button>
        </div>
        <div class="dialog-content">
          <form @submit.prevent="handleCreateKR">
            <div class="form-group">
              <label>标题</label>
              <input v-model="newKR.title" type="text" required class="form-input">
            </div>
            <div class="form-group">
              <label>描述</label>
              <textarea v-model="newKR.description" class="form-textarea"></textarea>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>目标值</label>
                <input v-model="newKR.target_value" type="number" step="0.1" class="form-input">
              </div>
              <div class="form-group">
                <label>当前值</label>
                <input v-model="newKR.current_value" type="number" step="0.1" value="0" class="form-input">
              </div>
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model="newKR.status" class="form-select">
                <option value="not_started">未开始</option>
                <option value="in_progress">进行中</option>
                <option value="completed">已完成</option>
                <option value="cancelled">已取消</option>
              </select>
            </div>
            <div class="dialog-footer">
              <button type="button" @click="showCreateKRDialogFlag = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">创建</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { taskAPI } from '../api/task'
import Toolbar from './Toolbar.vue'
import CustomDateTimePicker from './CustomDateTimePicker.vue'
import CustomDatePicker from './CustomDatePicker.vue'
import '../styles/variables.css'
import '../styles/dialog.css'

export default {
  name: 'TaskPage',
  components: {
    Toolbar,
    CustomDateTimePicker,
    CustomDatePicker
  },
  props: {
    username: {
      type: String,
      default: '用户'
    }
  },
  setup() {
    const router = useRouter()
    
    // 任务数据
    const tasks = ref([])
    const taskInstances = ref([])
    const okrs = ref([])
    const krs = ref([])

    // 筛选条件
    const taskTypeFilter = ref('all')
    const taskStatusFilter = ref('all')
    const taskPriorityFilter = ref('all')

    // 对话框状态
    const showCreateTaskDialog = ref(false)
    const showCreateKRDialogFlag = ref(false)

    // 新任务数据
    const newTask = ref({
      title: '',
      description: '',
      priority: 'medium',
      status: 'not_started',
      start_time: null,
      end_time: null,
      type: 'once'
    })

    // 新重复任务数据
    const newRecurringTask = ref({
      recurrence_type: 'daily',
      recurrence_interval: 1,
      recurrence_rule: '',
      recurrence_end_type: 'never',
      recurrence_end_date: null,
      recurrence_occurrences: null
    })

    // 新OKR数据
    const newOKR = ref({
      objective: '',
      description: '',
      start_date: null,
      end_date: null,
      status: 'draft'
    })

    // 新KR数据
    const newKR = ref({
      title: '',
      description: '',
      target_value: null,
      current_value: 0,
      status: 'not_started',
      okr_id: null
    })

    // 重复规则占位符
    const recurrenceRulePlaceholder = ref('例如: 每天重复无需规则, 每周重复填写 1,3,5 表示周一、周三、周五')

    // 星期几选项
    const weekdays = [
      { label: '周一', value: '1' },
      { label: '周二', value: '2' },
      { label: '周三', value: '3' },
      { label: '周四', value: '4' },
      { label: '周五', value: '5' },
      { label: '周六', value: '6' },
      { label: '周日', value: '7' }
    ]

    // 月份选项
    const months = [
      { label: '1月', value: '01' },
      { label: '2月', value: '02' },
      { label: '3月', value: '03' },
      { label: '4月', value: '04' },
      { label: '5月', value: '05' },
      { label: '6月', value: '06' },
      { label: '7月', value: '07' },
      { label: '8月', value: '08' },
      { label: '9月', value: '09' },
      { label: '10月', value: '10' },
      { label: '11月', value: '11' },
      { label: '12月', value: '12' }
    ]

    // 选中的星期几
    const selectedWeekdays = ref([])

    // 选中的月份日期
    const selectedMonthDays = ref([])

    // 选中的年份月份和日期
    const selectedMonth = ref('01')
    const selectedYearDays = ref([])

    // 展开的任务实例
    const expandedTaskInstances = ref([])

    // 监听重复任务结束类型变化，重置相关字段
    watch(() => newRecurringTask.value.recurrence_end_type, () => {
      // 重置所有结束类型相关的字段
      newRecurringTask.value.recurrence_end_date = null
      newRecurringTask.value.recurrence_occurrences = null
    })

    // 计算属性：筛选后的一次性任务
    const filteredTasks = computed(() => {
      if (taskTypeFilter.value !== 'all' && taskTypeFilter.value !== 'once') {
        return []
      }
      return tasks.value.filter(task => {
        const typeMatch = task.type === 'once' || task.type === 'okr_once'
        const statusMatch = taskStatusFilter.value === 'all' || task.status === taskStatusFilter.value
        const priorityMatch = taskPriorityFilter.value === 'all' || task.priority === taskPriorityFilter.value
        return typeMatch && statusMatch && priorityMatch
      })
    })

    // 计算属性：筛选后的重复任务
    const filteredRecurringTasks = computed(() => {
      if (taskTypeFilter.value !== 'all' && taskTypeFilter.value !== 'recurring') {
        return []
      }
      return tasks.value.filter(task => {
        const typeMatch = task.type === 'recurring' || task.type === 'okr_recurring'
        const statusMatch = taskStatusFilter.value === 'all' || task.status === taskStatusFilter.value
        const priorityMatch = taskPriorityFilter.value === 'all' || task.priority === taskPriorityFilter.value
        return typeMatch && statusMatch && priorityMatch
      })
    })

    // 计算属性：筛选后的OKR
    const filteredOKRs = computed(() => {
      if (taskTypeFilter.value !== 'all' && taskTypeFilter.value !== 'okrs') {
        return []
      }
      return okrs.value.filter(okr => {
        return taskStatusFilter.value === 'all' || okr.status === taskStatusFilter.value
      })
    })

    // 方法：切换星期几选择
    const toggleWeekday = (day) => {
      const index = selectedWeekdays.value.indexOf(day)
      if (index > -1) {
        selectedWeekdays.value.splice(index, 1)
      } else {
        selectedWeekdays.value.push(day)
      }
      // 更新重复规则
      updateRecurrenceRule()
    }

    // 方法：切换月份日期选择
    const toggleMonthDay = (day) => {
      const index = selectedMonthDays.value.indexOf(day)
      if (index > -1) {
        selectedMonthDays.value.splice(index, 1)
      } else {
        selectedMonthDays.value.push(day)
      }
      // 更新重复规则
      updateRecurrenceRule()
    }

    // 方法：选择月份
    const selectMonth = (month) => {
      selectedMonth.value = month
      // 重置日期选择
      selectedYearDays.value = []
      // 更新重复规则
      updateRecurrenceRule()
    }

    // 方法：切换年份日期选择
    const toggleYearDay = (day) => {
      const index = selectedYearDays.value.indexOf(day)
      if (index > -1) {
        selectedYearDays.value.splice(index, 1)
      } else {
        selectedYearDays.value.push(day)
      }
      // 更新重复规则
      updateRecurrenceRule()
    }

    // 方法：获取月份天数
    const getDaysInMonth = (month) => {
      const monthNum = parseInt(month)
      const daysInMonth = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
      return daysInMonth[monthNum - 1]
    }

    // 方法：更新重复规则
    const updateRecurrenceRule = () => {
      const type = newRecurringTask.value.recurrence_type
      let rule = ''
      
      switch (type) {
        case 'daily':
          rule = ''
          break
        case 'weekly':
          rule = selectedWeekdays.value.sort().join(',')
          break
        case 'monthly':
          rule = selectedMonthDays.value.sort((a, b) => a - b).join(',')
          break
        case 'yearly':
          rule = selectedYearDays.value.map(day => `${selectedMonth.value}-${day.toString().padStart(2, '0')}`).join(',')
          break
      }
      
      newRecurringTask.value.recurrence_rule = rule
    }

    // 方法：切换任务实例展开/折叠
    const toggleTaskInstances = (taskId) => {
      const index = expandedTaskInstances.value.indexOf(taskId)
      if (index > -1) {
        expandedTaskInstances.value.splice(index, 1)
      } else {
        expandedTaskInstances.value.push(taskId)
      }
    }

    // 方法：根据重复任务ID获取任务实例
    const getTaskInstancesByRecurringTask = (taskId) => {
      return taskInstances.value.filter(instance => instance.recurring_task_id === taskId)
    }

    // 方法：获取所有数据
    const fetchAllData = async () => {
      await fetchTasks()
    }

    // 方法：获取任务数据
    const fetchTasks = async () => {
      try {
        const response = await taskAPI.getTasks()
        tasks.value = response
      } catch (error) {
        console.error('获取任务失败:', error)
      }
    }

    // 方法：创建任务
    const handleCreateTask = async () => {
      try {
        if (newTask.value.type === 'okr') {
          // 创建OKR
          const okrResponse = await taskAPI.createOKR({
            objective: newTask.value.title,
            description: newTask.value.description,
            start_date: newOKR.value.start_date,
            end_date: newOKR.value.end_date,
            status: newOKR.value.status
          })
          await fetchTasks()
          
          // 重置表单
          resetForms()
          
          // 跳转到OKR详情页面
          router.push(`/okr-detail/${okrResponse.id}`)
        } else {
          // 创建基础任务
          const taskResponse = await taskAPI.createTask(newTask.value)
          
          // 如果是重复任务，创建重复任务详情
          if (newTask.value.type === 'recurring') {
            await taskAPI.createRecurringTask(taskResponse.id, newRecurringTask.value)
          }
          
          await fetchTasks()
          
          // 重置表单
          resetForms()
          
          // 跳转到任务详情页面继续填写
          if (newTask.value.type === 'recurring') {
            router.push(`/recurring-task-detail/${taskResponse.id}`)
          } else {
            router.push(`/task-detail/${taskResponse.id}`)
          }
        }
        
        showCreateTaskDialog.value = false
      } catch (error) {
        console.error('创建任务失败:', error)
        alert('创建任务失败，请重试')
      }
    }

    // 方法：重置表单
    const resetForms = () => {
      Object.assign(newTask.value, {
        title: '',
        description: '',
        priority: 'medium',
        status: 'not_started',
        start_time: null,
        end_time: null,
        type: 'once'
      })
      
      Object.assign(newRecurringTask.value, {
        recurrence_type: 'daily',
        recurrence_interval: 1,
        recurrence_rule: '',
        recurrence_end_type: 'never',
        recurrence_end_date: null,
        recurrence_occurrences: null
      })
      
      Object.assign(newOKR.value, {
        objective: '',
        description: '',
        start_date: null,
        end_date: null,
        status: 'draft'
      })
      
      // 重置选择
      selectedWeekdays.value = []
      selectedMonthDays.value = []
      selectedMonth.value = '01'
      selectedYearDays.value = []
    }

    // 方法：创建KR
    const handleCreateKR = async () => {
      try {
        await taskAPI.createKR(newKR.value)
        await fetchTasks()
        showCreateKRDialogFlag.value = false
        // 重置表单
        Object.assign(newKR.value, {
          title: '',
          description: '',
          target_value: null,
          current_value: 0,
          status: 'not_started',
          okr_id: null
        })
      } catch (error) {
        console.error('创建KR失败:', error)
      }
    }

    // 方法：删除任务
    const deleteTask = async (taskId) => {
      if (confirm('确定要删除这个任务吗？')) {
        try {
          await taskAPI.deleteTask(taskId)
          await fetchTasks()
        } catch (error) {
          console.error('删除任务失败:', error)
        }
      }
    }

    // 方法：编辑任务
    const editTask = (task) => {
      // 简化实现，实际项目中可以添加编辑对话框
      console.log('编辑任务:', task)
    }

    // 方法：编辑重复任务
    const editRecurringTask = (task) => {
      // 简化实现，实际项目中可以添加编辑对话框
      console.log('编辑重复任务:', task)
    }

    // 方法：编辑任务实例
    const editTaskInstance = (instance) => {
      // 简化实现，实际项目中可以添加编辑对话框
      console.log('编辑任务实例:', instance)
    }

    // 方法：编辑OKR
    const editOKR = (okr) => {
      // 简化实现，实际项目中可以添加编辑对话框
      console.log('编辑OKR:', okr)
    }

    // 方法：编辑KR
    const editKR = (kr) => {
      // 简化实现，实际项目中可以添加编辑对话框
      console.log('编辑KR:', kr)
    }

    // 方法：显示创建KR对话框
    const showCreateKRDialog = (okrId) => {
      newKR.value.okr_id = okrId
      showCreateKRDialogFlag.value = true
    }
    
    // 方法：跳转到任务详情页面
    const goToTaskDetail = (taskId) => {
      router.push(`/task-detail/${taskId}`)
    }
    
    // 方法：跳转到重复任务详情页面
    const goToRecurringTaskDetail = (taskId) => {
      router.push(`/recurring-task-detail/${taskId}`)
    }
    
    // 方法：跳转到OKR详情页面
    const goToOKRDetail = (okrId) => {
      router.push(`/okr-detail/${okrId}`)
    }

    // 方法：更新重复规则占位符
    const updateRecurrenceRulePlaceholder = () => {
      const type = newRecurringTask.value.recurrence_type
      switch (type) {
        case 'daily':
          recurrenceRulePlaceholder.value = '每天重复无需规则'
          break
        case 'weekly':
          recurrenceRulePlaceholder.value = '例如: 1,3,5 表示周一、周三、周五'
          break
        case 'monthly':
          recurrenceRulePlaceholder.value = '例如: 15,20 表示每月15号和20号'
          break
        case 'yearly':
          recurrenceRulePlaceholder.value = '例如: 01-01,02-28 表示每年1月1日和2月28日'
          break
        default:
          recurrenceRulePlaceholder.value = '请输入重复规则'
      }
      // 重置选择
      selectedWeekdays.value = []
      selectedMonthDays.value = []
      selectedMonth.value = '01'
      selectedYearDays.value = []
      // 清空规则
      newRecurringTask.value.recurrence_rule = ''
    }

    // 方法：获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        not_started: '未开始',
        in_progress: '进行中',
        completed: '已完成',
        cancelled: '已取消',
        overdue: '已过期',
        active: '激活',
        inactive: ' inactive',
        draft: '草稿'
      }
      return statusMap[status] || status
    }

    // 方法：获取优先级文本
    const getPriorityText = (priority) => {
      const priorityMap = {
        low: '低',
        medium: '中',
        high: '高'
      }
      return priorityMap[priority] || priority
    }

    // 方法：获取重复文本
    const getRecurrenceText = (task) => {
      if (!task.recurring_task) return ''
      
      const typeMap = {
        daily: '每天',
        weekly: '每周',
        monthly: '每月',
        yearly: '每年'
      }
      let text = `${typeMap[task.recurring_task.recurrence_type]}`
      if (task.recurring_task.recurrence_end_type === 'never') {
        text += '，永不结束'
      } else if (task.recurring_task.recurrence_end_type === 'on_date' && task.recurring_task.recurrence_end_date) {
        text += `，截止到 ${task.recurring_task.recurrence_end_date}`
      } else if (task.recurring_task.recurrence_end_type === 'after_occurrences' && task.recurring_task.recurrence_occurrences) {
        text += `，共 ${task.recurring_task.recurrence_occurrences} 次`
      }
      return text
    }

    // 方法：根据OKR ID获取KR列表
    const getKRsByOKR = (okrId) => {
      return krs.value.filter(kr => kr.okr_id === okrId)
    }

    // 方法：获取OKR相关的待办任务数量
    const getTodoCountByOKR = () => {
      // 简化实现，实际项目中可能需要根据OKR ID关联任务
      return tasks.value.filter(task => task.status === 'not_started').length
    }

    // 方法：格式化日期
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

    // 生命周期：组件挂载时获取数据
    onMounted(async () => {
      await fetchAllData()
    })

    return {
      // 数据
      tasks,
      taskInstances,
      okrs,
      krs,
      taskTypeFilter,
      taskStatusFilter,
      taskPriorityFilter,
      showCreateTaskDialog,
      showCreateKRDialogFlag,
      newTask,
      newRecurringTask,
      newOKR,
      newKR,
      recurrenceRulePlaceholder,
      weekdays,
      months,
      selectedWeekdays,
      selectedMonthDays,
      selectedMonth,
      selectedYearDays,
      expandedTaskInstances,
      
      // 计算属性
      filteredTasks,
      filteredRecurringTasks,
      filteredOKRs,
      
      // 方法
      fetchAllData,
      handleCreateTask,
      handleCreateKR,
      deleteTask,
      deleteOKR,
      deleteKR,
      editTask,
      editRecurringTask,
      editTaskInstance,
      editOKR,
      editKR,
      showCreateKRDialog,
      goToTaskDetail,
      goToRecurringTaskDetail,
      goToOKRDetail,
      updateRecurrenceRulePlaceholder,
      toggleWeekday,
      toggleMonthDay,
      selectMonth,
      toggleYearDay,
      getDaysInMonth,
      updateRecurrenceRule,
      toggleTaskInstances,
      getTaskInstancesByRecurringTask,
      getKRsByOKR,
      getTodoCountByOKR,
      getStatusText,
      getPriorityText,
      getRecurrenceText,
      formatDate,
      formatShortDate,
      resetForms
    }
  }
}
</script>

<style scoped>
.task-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
}

.page-content {
  padding: 80px 20px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  background: white;
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* 页面头部内容 - 包含标题和图例 */
.header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
  padding-left: 15px;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-primary {
  background-color: var(--color-task);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background-color: var(--color-task-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(74, 144, 226, 0.3);
}

.btn-secondary {
  background-color: var(--color-priority-medium);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background-color: #e69500;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(255, 165, 0, 0.3);
}

/* 重复任务按钮 */
.btn-recurring {
  background-color: var(--color-recurring);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-recurring:hover {
  background-color: var(--color-recurring-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(63, 173, 225, 0.3);
}

/* OKR按钮 */
.btn-okr {
  background-color: var(--color-okr);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-okr:hover {
  background-color: var(--color-okr-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid #ddd;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-sm:hover {
  background-color: #f8f9fa;
  transform: translateY(-1px);
}

.btn-sm.btn-danger {
  color: #ff6b6b;
  border-color: #ff6b6b;
}

.btn-sm.btn-danger:hover {
  background-color: #ff6b6b;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
}

/* 搜索条件样式 */
.task-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  background: white;
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

/* 搜索按钮的容器 */
.filter-item:last-child {
  margin-left: auto;
}

.filter-item label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.filter-select {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
}

.filter-select:hover {
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
}

/* 卡片列表样式 */
.task-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

/* 卡片样式 */
.task-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
  width: 320px;
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* 任务标题 - 固定宽度，超过显示省略号 */
.task-title {
  font-size: 16px;
  margin: 0;
  color: #333;
  font-weight: 600;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 一次性任务卡片头部背景颜色 */
.task-type-normal .card-header {
  background-color: var(--color-task-light);
}

/* 重复任务卡片头部背景颜色 */
.task-type-recurring .card-header {
  background-color: var(--color-recurring-light);
  border: 1px solid var(--color-recurring-border);
}

/* OKR卡片头部背景颜色 */
.task-type-okr .card-header {
  background-color: var(--color-okr-light);
}

/* 任务描述 - 固定宽度，超过显示省略号，增加高度到当前两倍 */
.task-description {
  font-size: 14px;
  margin: 0 0 15px 0;
  color: #666;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  min-height: 112px;
}

/* 搜索按钮样式 */
.btn-search {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  margin-top: 22px;
  margin-left: auto;
  margin-right: 20px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

/* 卡片标题容器 */
.card-title-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
  gap: 10px;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
}

.card-header h3 {
  font-size: 16px;
  margin: 0;
  color: #333;
  font-weight: 600;
  flex: 1;
}

/* 优先级指示器样式 */
.priority-indicator {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

/* 优先级文字 */
.priority-text {
  color: white;
  font-size: 12px;
  font-weight: 600;
}

/* 不同优先级的颜色 */
.priority-indicator.low {
  background-color: #4caf50;
}

.priority-indicator.medium {
  background-color: #ffa500;
}

.priority-indicator.high {
  background-color: #f44336;
}

.card-actions {
  display: flex;
  gap: 8px;
}

/* 卡片底部内容 - 时间和按钮在同一排 */
.card-footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  margin-top: auto;
  background-color: white;
  border-top: 1px solid #f0f0f0;
  position: relative;
}

/* 分隔线 - 两侧渐隐效果 */
.card-footer-content::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(to right, transparent, #e0e0e0, transparent);
}

/* 卡片底部的时间显示 */
.card-footer-content .card-time {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 卡片底部的操作按钮 */
.card-footer-content .card-actions {
  display: flex;
  gap: 10px;
}

/* 完成按钮 */
.btn-complete {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-complete:hover {
  background-color: #357abd;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(74, 145, 226, 0.3);
}

/* 取消按钮 */
.btn-cancel {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-cancel:hover {
  background-color: #d32f2f;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(244, 67, 54, 0.3);
}

/* 图例样式 */
.task-legend {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 10px 15px;
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 15px;
}

.legend-items {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  flex: 1;
}

.legend-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #3f3f3f;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 4px;
}

.legend-color.not_started {
  background-color: #ffc107;
}

.legend-color.in_progress {
  background-color: #4a90e2;
}

.legend-color.completed {
  background-color: #28a745;
}

.legend-color.cancelled {
  background-color: #6c757d;
}

.legend-color.overdue {
  background-color: #ff6b6b;
}

/* 卡片主体 */
.card-body {
  padding: 15px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-body p {
  font-size: 14px;
  margin: 0 0 15px 0;
  color: #666;
  line-height: 1.4;
}

.card-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 15px;
}

/* 时间显示样式 */
.card-time {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 时间徽章默认样式 */
.time-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 16px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

/* 未开始状态时间徽章 */
.task-card.not_started .time-badge {
  color: #212529;
  background-color: #ffc107;
  border-color: #ffc107;
}

.task-card.not_started .time-badge:hover {
  background-color: #e0a800;
  border-color: #d39e00;
}

/* 进行中状态时间徽章 */
.task-card.in_progress .time-badge {
  color: white;
  background-color: #4a90e2;
  border-color: #4a90e2;
}

.task-card.in_progress .time-badge:hover {
  background-color: #357abd;
  border-color: #2d6cb0;
}

/* 已完成状态时间徽章 */
.task-card.completed .time-badge {
  color: white;
  background-color: #28a745;
  border-color: #28a745;
}

.task-card.completed .time-badge:hover {
  background-color: #218838;
  border-color: #1e7e34;
}

/* 已取消状态时间徽章 */
.task-card.cancelled .time-badge {
  color: white;
  background-color: #6c757d;
  border-color: #6c757d;
}

.task-card.cancelled .time-badge:hover {
  background-color: #5a6268;
  border-color: #545b62;
}

/* 已过期状态时间徽章 */
.task-card.overdue .time-badge {
  color: white;
  background-color: #dc3545;
  border-color: #dc3545;
}

.task-card.overdue .time-badge:hover {
  background-color: #c82333;
  border-color: #bd2130;
}

/* 重复任务卡片状态样式 */
.task-card.task-type-recurring.active {
  border-left: 4px solid #4a90e2;
}

.task-card.task-type-recurring.inactive {
  border-left: 4px solid #6c757d;
  opacity: 0.7;
}

/* OKR卡片状态样式 */
.task-card.task-type-okr.draft {
  border-left: 4px solid #ffc107;
}

.task-card.task-type-okr.active {
  border-left: 4px solid #4a90e2;
}

.task-card.task-type-okr.completed {
  border-left: 4px solid #28a745;
}

.task-card.task-type-okr.cancelled {
  border-left: 4px solid #6c757d;
  opacity: 0.7;
}

/* 重复任务实例列表样式 */
.task-instances-list {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.task-instances-list h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
}

.instance-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.instance-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 10px;
  border: 1px solid #e9ecef;
}

.instance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.instance-header h5 {
  margin: 0;
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.instance-body {
  font-size: 12px;
  color: #666;
}

.instance-time {
  margin-top: 5px;
}

/* KR列表样式 */
.kr-list {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.kr-list h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
}

.kr-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #e9ecef;
}

.kr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.kr-header h5 {
  margin: 0;
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.kr-actions {
  display: flex;
  gap: 5px;
}

.kr-body {
  font-size: 12px;
  color: #666;
}

.kr-meta {
  margin-top: 5px;
  font-size: 11px;
  color: #888;
}

.kr-progress {
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 16px;
}

.empty-state.small {
  padding: 20px 10px;
  font-size: 14px;
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  border-radius: 12px 12px 0 0;
}

.dialog-header.task {
  background-color: var(--color-task-light);
}

.dialog-header.recurring {
  background-color: var(--color-recurring-light);
}

.dialog-header.okr {
  background-color: var(--color-okr-light);
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
  font-weight: 600;
}

.dialog-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.dialog-close:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: #333;
}

.dialog-content {
  padding: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #f0f0f0;
  border-radius: 0 0 12px 12px;
}

/* 表单样式 */
.form-group {
  margin-bottom: 15px;
}

.form-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.form-row .form-group {
  flex: 1;
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  min-height: 100px;
  transition: all 0.3s ease;
}

.form-textarea:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
}

.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.form-select:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
}

/* 重复规则选择器样式 */
.rule-description {
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 8px;
  font-size: 13px;
  color: #666;
  border: 1px solid #e9ecef;
}

.weekday-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.weekday-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.weekday-btn:hover {
  border-color: #4a90e2;
  background-color: #f0f7ff;
}

.weekday-btn.selected {
  background-color: #4a90e2;
  color: white;
  border-color: #4a90e2;
}

.calendar-selector {
  margin-top: 10px;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 5px;
  margin-top: 5px;
}

.calendar-day {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.calendar-day:hover {
  border-color: #4a90e2;
  background-color: #f0f7ff;
}

.calendar-day.selected {
  background-color: #4a90e2;
  color: white;
  border-color: #4a90e2;
}

.month-selector {
  margin-bottom: 10px;
}

.month-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
  margin-top: 5px;
}

.month-btn {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.month-btn:hover {
  border-color: #4a90e2;
  background-color: #f0f7ff;
}

.month-btn.selected {
  background-color: #4a90e2;
  color: white;
  border-color: #4a90e2;
}

.day-selector {
  margin-top: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-content {
    padding: 60px 10px 10px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .task-filters {
    flex-direction: column;
  }

  .filter-item {
    width: 100%;
  }

  .filter-select {
    width: 100%;
  }

  .task-cards {
    grid-template-columns: 1fr;
  }

  .task-card {
    width: 100%;
  }

  .form-row {
    flex-direction: column;
  }

  .weekday-selector {
    justify-content: center;
  }

  .calendar-grid {
    grid-template-columns: repeat(7, 1fr);
  }

  .month-buttons {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
