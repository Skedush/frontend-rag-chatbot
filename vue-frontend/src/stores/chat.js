/**
 * Chat Store - Pinia 全局状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatStream, parseStream } from '../api/chat'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref([])
  const isStreaming = ref(false)
  const sources = ref([])

  // 添加用户消息
  function addUserMessage(content) {
    messages.value.push({
      role: 'user',
      content,
      timestamp: Date.now()
    })
  }

  // 添加助手消息
  function addAssistantMessage(content) {
    messages.value.push({
      role: 'assistant',
      content,
      timestamp: Date.now()
    })
  }

  // 更新最后一条助手消息（流式更新）
  function updateLastAssistantMessage(content) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content = content
    }
  }

  // 发送消息并处理流式响应
  async function sendMessage(question) {
    if (isStreaming.value) return

    isStreaming.value = true
    sources.value = []
    addUserMessage(question)
    addAssistantMessage('')

    try {
      const response = await chatStream(question)

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }

      let fullContent = ''

      for await (const chunk of parseStream(response)) {
        if (chunk.content) {
          fullContent += chunk.content
          updateLastAssistantMessage(fullContent)
        }
        if (chunk.sources) {
          sources.value = chunk.sources
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      updateLastAssistantMessage(`抱歉，发生了错误：${error.message}`)
    } finally {
      isStreaming.value = false
    }
  }

  // 清空聊天记录
  function clearMessages() {
    messages.value = []
    sources.value = []
  }

  return {
    messages,
    isStreaming,
    sources,
    sendMessage,
    clearMessages
  }
})
