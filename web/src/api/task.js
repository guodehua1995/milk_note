// api/task.js
import api from './index'

/**
 * 任务管理相关API调用
 */
export const taskAPI = {
  /**
   * 创建新事项
   * @param {Object} taskData - 任务数据
   * @returns {Promise}
   */
  createTask: (taskData) => {
    return api.post('/tasks', taskData)
  },

  /**
   * 获取用户的所有事项
   * @param {string} taskType - 事项类型（可选）
   * @returns {Promise}
   */
  getTasks: (taskType = null) => {
    const url = taskType ? `/tasks?task_type=${taskType}` : '/tasks'
    return api.get(url)
  },

  /**
   * 获取指定事项详情
   * @param {number} taskId - 任务ID
   * @returns {Promise}
   */
  getTask: (taskId) => {
    return api.get(`/tasks/${taskId}`)
  },

  /**
   * 更新事项
   * @param {number} taskId - 任务ID
   * @param {Object} taskData - 任务数据
   * @returns {Promise}
   */
  updateTask: (taskId, taskData) => {
    return api.put(`/tasks/${taskId}`, taskData)
  },

  /**
   * 删除事项
   * @param {number} taskId - 任务ID
   * @returns {Promise}
   */
  deleteTask: (taskId) => {
    return api.delete(`/tasks/${taskId}`)
  },

  /**
   * 创建一次性事项详情
   * @param {number} taskId - 任务ID
   * @param {Object} onceTaskData - 一次性事项数据
   * @returns {Promise}
   */
  createOnceTask: (taskId, onceTaskData) => {
    return api.post(`/tasks/${taskId}/once`, onceTaskData)
  },

  /**
   * 更新一次性事项详情
   * @param {number} taskId - 任务ID
   * @param {Object} onceTaskData - 一次性事项数据
   * @returns {Promise}
   */
  updateOnceTask: (taskId, onceTaskData) => {
    return api.put(`/tasks/${taskId}/once`, onceTaskData)
  },

  /**
   * 创建重复事项详情
   * @param {number} taskId - 任务ID
   * @param {Object} recurringTaskData - 重复事项数据
   * @returns {Promise}
   */
  createRecurringTask: (taskId, recurringTaskData) => {
    return api.post(`/tasks/${taskId}/recurring`, recurringTaskData)
  },

  /**
   * 更新重复事项详情
   * @param {number} taskId - 任务ID
   * @param {Object} recurringTaskData - 重复事项数据
   * @returns {Promise}
   */
  updateRecurringTask: (taskId, recurringTaskData) => {
    return api.put(`/tasks/${taskId}/recurring`, recurringTaskData)
  },

  /**
   * 获取任务实例
   * @param {number} recurringTaskId - 重复任务ID（可选）
   * @returns {Promise}
   */
  getTaskInstances: (recurringTaskId = null) => {
    const url = recurringTaskId ? `/task-instances?recurring_task_id=${recurringTaskId}` : '/task-instances'
    return api.get(url)
  },

  /**
   * 更新任务实例
   * @param {number} instanceId - 实例ID
   * @param {Object} instanceData - 实例数据
   * @returns {Promise}
   */
  updateTaskInstance: (instanceId, instanceData) => {
    return api.put(`/task-instances/${instanceId}`, instanceData)
  },

  /**
   * 创建OKR
   * @param {Object} okrData - OKR数据
   * @returns {Promise}
   */
  createOKR: (okrData) => {
    return api.post('/okrs', okrData)
  },

  /**
   * 获取用户的所有OKR
   * @returns {Promise}
   */
  getOKRs: () => {
    return api.get('/okrs')
  },

  /**
   * 获取指定OKR详情
   * @param {number} okrId - OKR ID
   * @returns {Promise}
   */
  getOKR: (okrId) => {
    return api.get(`/okrs/${okrId}`)
  },

  /**
   * 更新OKR
   * @param {number} okrId - OKR ID
   * @param {Object} okrData - OKR数据
   * @returns {Promise}
   */
  updateOKR: (okrId, okrData) => {
    return api.put(`/okrs/${okrId}`, okrData)
  },

  /**
   * 删除OKR
   * @param {number} okrId - OKR ID
   * @returns {Promise}
   */
  deleteOKR: (okrId) => {
    return api.delete(`/okrs/${okrId}`)
  },

  /**
   * 创建KR
   * @param {Object} krData - KR数据
   * @returns {Promise}
   */
  createKR: (krData) => {
    return api.post('/krs', krData)
  },

  /**
   * 获取KR列表
   * @param {number} okrId - OKR ID（可选）
   * @returns {Promise}
   */
  getKRs: (okrId = null) => {
    const url = okrId ? `/krs?okr_id=${okrId}` : '/krs'
    return api.get(url)
  },

  /**
   * 更新KR
   * @param {number} krId - KR ID
   * @param {Object} krData - KR数据
   * @returns {Promise}
   */
  updateKR: (krId, krData) => {
    return api.put(`/krs/${krId}`, krData)
  },

  /**
   * 删除KR
   * @param {number} krId - KR ID
   * @returns {Promise}
   */
  deleteKR: (krId) => {
    return api.delete(`/krs/${krId}`)
  },

  /**
   * 创建KR与任务的关联
   * @param {Object} krTaskData - 关联数据
   * @returns {Promise}
   */
  createKRTask: (krTaskData) => {
    return api.post('/kr-tasks', krTaskData)
  },

  /**
   * 获取KR与任务的关联
   * @param {number} krId - KR ID（可选）
   * @returns {Promise}
   */
  getKRTasks: (krId = null) => {
    const url = krId ? `/kr-tasks?kr_id=${krId}` : '/kr-tasks'
    return api.get(url)
  },

  /**
   * 删除KR与任务的关联
   * @param {number} krTaskId - 关联ID
   * @returns {Promise}
   */
  deleteKRTask: (krTaskId) => {
    return api.delete(`/kr-tasks/${krTaskId}`)
  }
}
