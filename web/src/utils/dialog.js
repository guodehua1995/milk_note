/**
 * 弹窗通用工具函数
 */

/**
 * 显示弹窗
 * @param {Ref} dialogRef - 弹窗显示状态的ref
 */
export const showDialog = (dialogRef) => {
  dialogRef.value = true;
};

/**
 * 隐藏弹窗
 * @param {Ref} dialogRef - 弹窗显示状态的ref
 */
export const hideDialog = (dialogRef) => {
  dialogRef.value = false;
};

/**
 * 重置表单数据
 * @param {Ref} formRef - 表单数据的ref
 * @param {Object} defaultValues - 默认值对象
 */
export const resetForm = (formRef, defaultValues) => {
  Object.assign(formRef.value, defaultValues);
};

/**
 * 处理弹窗外部点击事件
 * @param {Event} event - 点击事件对象
 * @param {Ref} dialogRef - 弹窗显示状态的ref
 * @param {string} dialogSelector - 弹窗选择器
 */
export const handleOutsideClick = (event, dialogRef, dialogSelector = '.dialog') => {
  if (!event.target.closest(dialogSelector)) {
    hideDialog(dialogRef);
  }
};

/**
 * 格式化日期为本地字符串
 * @param {string} dateString - 日期字符串
 * @returns {string} 格式化后的日期字符串
 */
export const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN');
};

/**
 * 获取状态文本
 * @param {string} status - 状态值
 * @returns {string} 状态文本
 */
export const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消',
    overdue: '已过期',
    active: '激活',
    inactive: ' inactive',
    draft: '草稿'
  };
  return statusMap[status] || status;
};

/**
 * 获取优先级文本
 * @param {string} priority - 优先级值
 * @returns {string} 优先级文本
 */
export const getPriorityText = (priority) => {
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高'
  };
  return priorityMap[priority] || priority;
};

/**
 * 确认对话框
 * @param {string} message - 确认消息
 * @param {Function} callback - 确认后的回调函数
 */
export const confirmDialog = (message, callback) => {
  if (confirm(message)) {
    callback();
  }
};
