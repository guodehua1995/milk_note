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