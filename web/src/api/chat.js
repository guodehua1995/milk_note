// api/chat.js
import api from './index'

export const chatAPI = {
  // 发送消息 - 返回Promise，但实际处理在组件中使用fetch
  sendMessage: (input) => {
    return api.post('/chat/send', {
      input
    })
  },

  // 获取聊天历史
  getChatHistory: (page = 1, page_size = 10) => {
    return api.get('/chat/history', {
      params: {
        page,
        page_size
      }
    })
  },

  // 创建新的聊天会话
  createChatSession: (sessionName) => {
    return api.post('/chat/session', {
      session_name: sessionName
    })
  },

  // 获取聊天会话列表
  getChatSessions: () => {
    return api.get('/chat/sessions')
  }
}

// 文档相关API
export const documentAPI = {
  // 上传文档
  uploadDocument: (file, task_id = null) => {
    const formData = new FormData()
    formData.append('file', file)
    if (task_id) {
      formData.append('task_id', task_id)
    }
    return api.post('/document/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          return percentCompleted
        }
      }
    })
  },

  // 获取文档列表
  getDocuments: (page = 1, page_size = 10, task_id = null) => {
    return api.get('/document/list', {
      params: {
        page,
        page_size,
        task_id
      }
    })
  },

  // 获取文档状态
  getDocumentStatus: (document_id) => {
    return api.get(`/document/status/${document_id}`)
  },

  // 删除文档
  deleteDocument: (document_id) => {
    return api.delete(`/document/${document_id}`)
  },

  // 批量删除文档
  batchDeleteDocuments: (document_ids) => {
    return api.delete('/document/batch/delete', {
      params: {
        document_ids
      }
    })
  },

  // 获取文档切片
  getDocumentChunks: (document_id) => {
    return api.get(`/document/${document_id}/chunks`)
  }
}