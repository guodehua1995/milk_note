// api/task.js
import api from './index'

/**
 * 获取任务列表
 * @param {Object} params - 查询参数
 * @param {number} params.skip - 跳过的记录数
 * @param {number} params.limit - 返回的最大记录数
 * @param {boolean} params.include_subtasks - 是否包含子任务
 * @returns {Promise} - 返回任务列表
 */
export const getTasks = (params = {}) => {
  return api.get('/tasks', { params })
}

/**
 * 获取任务详情
 * @param {number} taskId - 任务ID
 * @returns {Promise} - 返回任务详情
 */
export const getTaskDetail = (taskId) => {
  return api.get(`/tasks/${taskId}`)
}

/**
 * 创建任务
 * @param {Object} taskData - 任务数据
 * @returns {Promise} - 返回创建的任务
 */
export const createTask = (taskData) => {
  return api.post('/tasks', taskData)
}

/**
 * 更新任务
 * @param {number} taskId - 任务ID
 * @param {Object} taskData - 任务数据
 * @returns {Promise} - 返回更新后的任务
 */
export const updateTask = (taskId, taskData) => {
  return api.put(`/tasks/${taskId}`, taskData)
}

/**
 * 取消任务
 * @param {number} taskId - 任务ID
 * @returns {Promise} - 返回取消后的任务
 */
export const cancelTask = (taskId) => {
  return api.put(`/tasks/${taskId}/cancel`)
}

/**
 * 计算任务进度
 * @param {number} taskId - 任务ID
 * @returns {Promise} - 返回任务进度
 */
export const calculateTaskProgress = (taskId) => {
  return api.get(`/tasks/${taskId}/progress`)
}

/**
 * AI规划任务
 * @param {number} taskId - 任务ID
 * @returns {Promise} - 返回AI规划结果
 */
export const aiPlanTask = (taskId) => {
  return api.post(`/tasks/${taskId}/ai-plan`)
}

/**
 * 获取执行情况列表
 * @param {number} taskId - 任务ID
 * @param {Object} params - 查询参数
 * @returns {Promise} - 返回执行情况列表
 */
export const getExecutions = (taskId, params = {}) => {
  return api.get(`/tasks/${taskId}/executions`, { params })
}

/**
 * 创建执行情况
 * @param {number} taskId - 任务ID
 * @param {Object} executionData - 执行情况数据
 * @returns {Promise} - 返回创建的执行情况
 */
export const createExecution = (taskId, executionData) => {
  return api.post(`/tasks/${taskId}/executions`, executionData)
}

/**
 * 批量创建执行情况
 * @param {number} taskId - 任务ID
 * @param {Object} batchData - 批量执行情况数据
 * @returns {Promise} - 返回创建的执行情况列表
 */
export const batchCreateExecutions = (taskId, batchData) => {
  return api.post(`/tasks/${taskId}/executions/batch`, batchData)
}

/**
 * 任务对话
 * @param {Object} message - 对话消息
 * @returns {Promise} - 返回对话结果
 */
export const taskChat = (message) => {
  return api.post('/tasks/chat', message)
}

/**
 * 获取任务的子任务树
 * @param {number} taskId - 任务ID
 * @returns {Promise} - 返回子任务树结构
 */
export const getTaskSubtasks = (taskId) => {
  return api.get(`/tasks/${taskId}/subtasks`)
}