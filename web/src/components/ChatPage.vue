<template>
  <div class="chat-container">
    <Toolbar :username="username" />
    <!-- 顶部导航栏 -->
    <div class="chat-header">
      <div class="header-content">
        <div class="user-info">
          <div class="avatar">
            <span class="initial">{{ userInitial }}</span>
          </div>
          <div class="user-details">
            <h3>{{ username }}</h3>
            <p class="status">在线</p>
          </div>
        </div>
        <div class="header-actions">
          <button class="action-btn">
            <i class="icon">⚙️</i>
          </button>
          <button class="action-btn">
            <i class="icon">👤</i>
          </button>
        </div>
      </div>
    </div>

    <!-- 聊天内容区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(message, index) in messages" 
        :key="index" 
        :class="['message', message.sender]"
      >
        <div class="message-avatar" v-if="message.sender === 'bot'">
          <span class="bot-initial">🤖</span>
        </div>
        <div class="message-content">
          <div 
            class="message-text" 
            :class="{ 'is-loading': message.isTyping }"
          >
            <div v-if="message.isTyping" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div v-else v-html="formatMessage(message.content)"></div>
          </div>
          <div class="message-time" v-if="!message.isTyping">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
        <div class="message-avatar" v-if="message.sender === 'user'">
          <span class="initial">{{ userInitial }}</span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-container">
        <textarea
          v-model="inputMessage"
          @keydown.enter="handleEnterKey"
          placeholder="输入消息..."
          class="message-input"
          rows="1"
          :style="{ height: inputHeight }"
        ></textarea>
        <button 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || sending"
          class="send-btn"
        >
          <span v-if="!sending">➤</span>
          <span v-else class="loading-dot">●</span>
        </button>
      </div>
      <div class="input-actions">
        <button class="action-btn">
          <i class="icon">📎</i>
        </button>
        <button class="action-btn">
          <i class="icon">😊</i>
        </button>
        <button class="action-btn">
          <i class="icon">📷</i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { chatAPI } from '../api/chat'
import { marked } from 'marked'
import Toolbar from './Toolbar.vue'

export default {
  components: {
    Toolbar
  },
  name: 'ChatPage',
  props: {
    username: {
      type: String,
      default: '用户'
    }
  },
  data() {
    return {
      inputMessage: '',
      inputHeight: '50px',
      sending: false,
      messages: [
        {
          sender: 'bot',
          content: '你好！我是MilkNote助手，有什么可以帮助你的吗？',
          timestamp: new Date(Date.now() - 300000) // 5分钟前
        }
      ]
    }
  },
  computed: {
    userInitial() {
      return this.username.charAt(0).toUpperCase()
    }
  },
  async mounted() {
    this.scrollToBottom()
    // 监听输入框高度变化
    this.$nextTick(() => {
      this.adjustInputHeight()
    })
    
    // 加载聊天历史
    await this.loadChatHistory()
  },
  updated() {
    this.scrollToBottom()
  },
  methods: {
    formatTime(date) {
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      
      if (minutes < 1) return '刚刚'
      if (minutes < 60) return `${minutes}分钟前`
      if (minutes < 1440) return `${Math.floor(minutes / 60)}小时前` // 24小时内
      
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    },
    formatMessage(text) {
      // 使用marked库解析markdown文本
      return marked.parse(text) || ''
    },
    adjustInputHeight() {
      const textarea = this.$el.querySelector('.message-input')
      if (textarea) {
        textarea.style.height = 'auto'
        const scrollHeight = textarea.scrollHeight
        this.inputHeight = `${Math.min(scrollHeight, 120)}px`
      }
    },
    handleEnterKey(event) {
      if (event.shiftKey) {
        // 按住Shift+Enter换行
        return
      }
      event.preventDefault()
      this.sendMessage()
    },
    async sendMessage() {
      if (!this.inputMessage.trim() || this.sending) return
      
      const userMessage = {
        sender: 'user',
        content: this.inputMessage,
        timestamp: new Date()
      }
      
      // 添加用户消息到聊天记录
      this.messages.push(userMessage)
      const userInput = this.inputMessage
      this.inputMessage = ''
      this.adjustInputHeight()
      
      // 模拟发送消息
      this.sending = true
      
      try {
        // 添加一个正在输入的提示
        const typingMessage = {
          sender: 'bot',
          isTyping: true,
          timestamp: new Date()
        }
        this.messages.push(typingMessage)
        
        // 调用真实的API - 使用fetch处理流式响应
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000'}/api/chat/send`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ input: userInput })
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        // 移除正在输入的提示
        this.messages.pop()
        
        // 添加机器人回复消息（初始为空）
        const botResponse = {
          sender: 'bot',
          content: '',
          timestamp: new Date()
        }
        const botMessageIndex = this.messages.push(botResponse) - 1
        
        // 处理流式响应
        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')  // 明确指定UTF-8编码
        let done = false
        let buffer = ''  // 用于处理可能的分割字符
        
        while (!done) {
          const { value, done: readerDone } = await reader.read()
          done = readerDone
          
          if (value) {
            const chunk = decoder.decode(value, { stream: !done })  // 对于最后一个块，不使用stream模式
            // console.log('Received chunk:', chunk)
            // 将块添加到缓冲区
            buffer += chunk+'\n'
            
            // 按行分割处理（因为后端可能返回多行JSON）
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''  // 保留最后一个不完整的行在缓冲区中
            
            for (const line of lines) {
              if (line.trim()) {  // 忽略空行
                try {
                  const data = JSON.parse(line)
                  // console.log('Parsed JSON:', data)

                  // 只更新内容部分，忽略其他类型的消息
                  if (data.type === 'assistant' && data.content) {
                    this.messages[botMessageIndex].content += data.content
                  } else if (data.type === 'start' || data.type === 'end') {
                    // 可以根据需要处理开始和结束消息
                    console.log('Stream event:', data.type, data.content)
                  }
                } catch (e) {
                  console.error('解析JSON失败:', e)
                  // 如果不是有效的JSON，直接添加到内容中
                  this.messages[botMessageIndex].content += line
                }
              }
            }
            
            // 滚动到底部以显示新内容
            this.scrollToBottom()
          }
        }
        
        // 处理缓冲区中剩余的内容
        if (buffer) {
          try {
            const data = JSON.parse(buffer)
            if (data.type === 'assistant' && data.content) {
              this.messages[botMessageIndex].content += data.content
            }
          } catch (e) {
            // 如果不是有效的JSON，直接添加到内容中
            this.messages[botMessageIndex].content += buffer
          }
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        // 移除正在输入的提示
        this.messages.pop()
        // 添加错误消息
        this.messages.push({
          sender: 'bot',
          content: '发送失败，请重试',
          timestamp: new Date()
        })
      } finally {
        this.sending = false
      }
    },
    async loadChatHistory() {
      try {
        // 加载最近的聊天历史
        const response = await chatAPI.getChatHistory(1, 10)
        if (response && response.history && response.history.length > 0) {
          // 清空默认消息并加载历史消息
          this.messages = response.history.map(msg => ({
            sender: msg.sender || (msg.type === 'assistant' ? 'bot' : 'user'),
            content: msg.content,
            timestamp: new Date(msg.timestamp || Date.now())
          }))
          this.scrollToBottom()
        }
      } catch (error) {
        console.error('加载聊天历史失败:', error)
        // 保持默认欢迎消息
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
        }
      })
    }
  },
  watch: {
    inputMessage() {
      this.adjustInputHeight()
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
  max-width: 800px;
  margin: 0 auto;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.1);
  border-radius: 20px;
  overflow: hidden;
  padding-top: 60px;
}

.chat-header {
  background: white;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar, .message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(45deg, #ff9a9e, #fad0c4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 16px;
}

.bot-initial {
  font-size: 24px;
}

.user-details h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.status {
  margin: 0;
  font-size: 12px;
  color: #4caf50;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: #e9ecef;
  transform: scale(1.05);
}

.icon {
  font-size: 18px;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #fafafa;
}

.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-text {
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
}

/* Markdown样式 - 圆润可爱风格 */
.message-text :deep(h1) {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0.6em 0 0.3em;
  color: #ff6b6b; /* 明亮的粉红色，与主题匹配 */
  border-bottom: 2px solid rgba(255, 107, 107, 0.3);
  padding-bottom: 0.2em;
  text-shadow: 0 1px 2px rgba(255, 107, 107, 0.2);
}

.message-text :deep(h2) {
  font-size: 1.3em;
  font-weight: bold;
  margin: 0.5em 0 0.2em;
  color: #ffa500; /* 明亮的橙色，与主题匹配 */
  border-bottom: 1px solid rgba(255, 165, 0, 0.25);
  padding-bottom: 0.1em;
  text-shadow: 0 1px 2px rgba(255, 165, 0, 0.2);
}

.message-text :deep(h3) {
  font-size: 1.1em;
  font-weight: bold;
  margin: 0.4em 0 0.2em;
  color: #4a90e2; /* 明亮的蓝色，与主题匹配 */
  text-shadow: 0 1px 2px rgba(74, 144, 226, 0.2);
}

.message-text :deep(p) {
  margin: 0.5em 0;
  line-height: 1.6;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.8em;
}

.message-text :deep(li) {
  margin: 0.35em 0;
  line-height: 1.5;
}

/* 自定义列表项样式 */
.message-text :deep(ul) {
  list-style-type: none;
  padding-left: 1.5em;
}

.message-text :deep(ul li) {
  position: relative;
  margin: 0.35em 0;
  line-height: 1.5;
}

.message-text :deep(ul li::before) {
  content: '✨';
  position: absolute;
  left: -1.3em;
  font-size: 0.8em;
  color: #ff6b6b;
}

.message-text :deep(ol) {
  list-style-type: decimal;
  padding-left: 1.8em;
}

.message-text :deep(ol li) {
  margin: 0.35em 0;
  line-height: 1.5;
  font-weight: 500;
}

.message-text :deep(code) {
  background-color: rgba(255, 107, 107, 0.15);
  padding: 0.25em 0.5em;
  border-radius: 6px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.message-text :deep(pre) {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 165, 0, 0.1));
  padding: 16px;
  border-radius: 12px;
  overflow-x: auto;
  margin: 0.7em 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 107, 107, 0.2);
}

.message-text :deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  box-shadow: none;
  font-size: 0.85em;
  line-height: 1.5;
}

.message-text :deep(blockquote) {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 165, 0, 0.08));
  border: none;
  border-radius: 10px;
  padding: 12px 16px;
  margin: 0.7em 0;
  color: inherit;
  font-style: normal;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.message-text :deep(blockquote::before) {
  content: '💬';
  margin-right: 0.5em;
  font-size: 1.1em;
  vertical-align: middle;
}

.message-text :deep(hr) {
  border: none;
  border-top: 2px dashed rgba(255, 107, 107, 0.2);
  margin: 1.2em 0;
}

.message-text :deep(a) {
  color: #ff6b6b;
  text-decoration: none;
  background: linear-gradient(transparent 80%, rgba(255, 107, 107, 0.2) 0);
  padding: 0 2px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.message-text :deep(a:hover) {
  background: linear-gradient(transparent 80%, rgba(255, 107, 107, 0.4) 0);
  color: #ff5252;
}

/* 加粗字体样式 - 淡蓝色圆润 */
.message-text :deep(strong) {
  color: #4a90e2;
  font-weight: bold;
  background-color: rgba(74, 144, 226, 0.1);
  padding: 0.15em 0.3em;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(74, 144, 226, 0.2);
  font-size: 1.05em;
}

.message-text :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
  margin: 0.7em 0;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.message-text :deep(img:hover) {
  transform: scale(1.02);
}

/* 为用户消息调整markdown样式（白色文字） */
.message.user .message-content .message-text :deep(code) {
  background-color: rgba(255, 255, 255, 0.25);
  color: white;
}

.message.user .message-content .message-text :deep(pre) {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.15));
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.message.user .message-content .message-text :deep(pre code) {
  color: white;
}

.message.user .message-content .message-text :deep(blockquote) {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.15));
  color: rgba(255, 255, 255, 0.9);
}

.message.user .message-content .message-text :deep(blockquote::before) {
  color: rgba(255, 255, 255, 0.8);
}

.message.user .message-content .message-text :deep(a) {
  color: rgba(255, 255, 255, 0.95);
  background: linear-gradient(transparent 80%, rgba(255, 255, 255, 0.3) 0);
}

.message.user .message-content .message-text :deep(a:hover) {
  background: linear-gradient(transparent 80%, rgba(255, 255, 255, 0.5) 0);
  color: white;
}

.message.user .message-content .message-text :deep(hr) {
  border-top-color: rgba(255, 255, 255, 0.3);
}

.message.user .message-content .message-text :deep(ul li::before) {
  color: rgba(255, 255, 255, 0.8);
}

/* 为用户消息中的加粗字体调整样式 */
.message.user .message-content .message-text :deep(strong) {
  color: rgba(255, 255, 255, 0.95);
  background-color: rgba(74, 144, 226, 0.3);
  box-shadow: 0 1px 2px rgba(74, 144, 226, 0.3);
}

/* 为用户消息中的标题调整样式 */
.message.user .message-content .message-text :deep(h1) {
  color: rgba(255, 255, 255, 0.95);
  border-bottom-color: rgba(255, 255, 255, 0.3);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.message.user .message-content .message-text :deep(h2) {
  color: rgba(255, 255, 255, 0.95);
  border-bottom-color: rgba(255, 255, 255, 0.25);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.message.user .message-content .message-text :deep(h3) {
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.message.user .message-content .message-text {
  background: linear-gradient(45deg, #ff6b6b, #ffa500);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.bot .message-content .message-text {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-time {
  font-size: 12px;
  color: #999;
  text-align: right;
  padding-right: 8px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
  height: 20px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  display: inline-block;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.chat-input-area {
  background: white;
  padding: 16px 20px 8px;
  border-top: 1px solid #f0f0f0;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 8px;
}

.message-input {
  flex: 1;
  border: 2px solid #e9ecef;
  border-radius: 20px;
  padding: 12px 16px;
  resize: none;
  outline: none;
  font-size: 15px;
  line-height: 1.4;
  max-height: 120px;
  transition: border-color 0.3s ease;
}

.message-input:focus {
  border-color: #ff6b6b;
}

.send-btn {
  width: 44px;
  height: 44px;
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

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.loading-dot {
  animation: pulse 1.4s infinite ease-in-out;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
}

.input-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-container {
    height: 100vh;
    border-radius: 0;
    max-width: 100%;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-actions {
    align-self: flex-end;
  }
}
</style>