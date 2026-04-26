/**
 * RAG Chatbot 前端主组件
 *
 * 功能：
 * 1. 管理聊天消息列表
 * 2. 处理用户输入和 AI 回复
 * 3. 文件上传功能
 * 4. 流式输出支持
 */

import React, { useState, useEffect } from 'react'
import MessageList from './components/MessageList'
import FileUpload from './components/FileUpload'
import ChatInput from './components/ChatInput'
import { chatStream, parseStream, getStats } from './api/chat'

/**
 * App 主组件
 *
 * 状态：
 * - messages: 聊天消息列表，每条消息包含 role、content、sources
 * - loading: 是否正在等待 AI 回复
 * - uploaded: 是否已上传文档（用于控制输入框可用状态）
 */
function App() {
  // 聊天消息列表
  // 格式：[{ role: 'user' | 'assistant', content: '...', sources: [...] }]
  const [messages, setMessages] = useState([])

  // 是否正在加载（等待 AI 回复）
  const [loading, setLoading] = useState(false)

  // 是否已上传文档
  // 初始为 false，用户上传后变为 true，刷新页面重置
  const [uploaded, setUploaded] = useState(false)

  /**
   * 组件挂载时检查向量库状态
   * 如果向量库已有数据，说明之前上传过文档
   */
  useEffect(() => {
    getStats()
      .then(result => {
        // getStats 返回 { status: 'success' } 表示向量库已就绪
        if (result.status === 'success') {
          setUploaded(true)
        }
      })
      .catch(() => {
        // 忽略错误，保持 uploaded=false
      })
  }, [])

  /**
   * 发送消息处理
   *
   * 流程：
   * 1. 将用户消息添加到列表
   * 2. 调用流式聊天 API
   * 3. 逐步更新 AI 回复（流式效果）
   * 4. 流结束后更新来源文档
   *
   * @param {string} question - 用户输入的问题
   */
  const handleSend = async (question) => {
    // 1. 添加用户消息到列表
    setMessages((prev) => [...prev, { role: 'user', content: question }])

    // 开始加载状态
    setLoading(true)

    try {
      // 2. 调用流式聊天 API
      const response = await chatStream(question)

      // 3. 添加一条空的 AI 消息占位
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '',          // 初始为空
          sources: [],          // 来源文档初始为空
          isStreaming: true    // 标记为正在流式输出
        }
      ])

      // 用于累积完整回复
      let fullContent = ''
      let sources = []

      // 4. 流式处理响应
      // parseStream 是一个生成器，逐步 yield 每个字符/词
      for await (const chunk of parseStream(response)) {
        if (chunk.content) {
          // 累积回复内容
          fullContent += chunk.content

          // 实时更新最后一条消息
          // 这样用户能看到逐字出现的回复
          setMessages((prev) => {
            const newMsgs = [...prev]
            newMsgs[newMsgs.length - 1] = {
              ...newMsgs[newMsgs.length - 1],
              content: fullContent
            }
            return newMsgs
          })
        }

        // 保存来源文档（在流结束时返回）
        if (chunk.sources && chunk.sources.length > 0) {
          sources = chunk.sources
        }
      }

      // 5. 流结束，更新状态
      setMessages((prev) => {
        const newMsgs = [...prev]
        newMsgs[newMsgs.length - 1] = {
          ...newMsgs[newMsgs.length - 1],
          isStreaming: false,  // 关闭流式标记
          sources: sources     // 更新来源文档
        }
        return newMsgs
      })

    } catch (error) {
      // 发生错误，显示错误消息
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `抱歉，发生错误: ${error.message}` }
      ])
    } finally {
      // 关闭加载状态
      setLoading(false)
    }
  }

  /**
   * 上传成功回调
   * 将 uploaded 设为 true，允许用户提问
   */
  const handleUploadSuccess = () => {
    setUploaded(true)
  }

  return (
    <div className="min-h-screen flex flex-col max-w-4xl mx-auto p-4">
      {/* 顶部标题 */}
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-center text-gray-800">
          Frontend RAG Chatbot
        </h1>
        <p className="text-center text-gray-500 text-sm mt-1">
          基于文档的智能问答系统
        </p>
      </header>

      {/* 文件上传组件 */}
      <FileUpload onUploadSuccess={handleUploadSuccess} />

      {/* 聊天消息区域 */}
      <div className="flex-1 bg-gray-50 rounded-lg shadow-inner mb-4 overflow-hidden">
        <MessageList messages={messages} />
      </div>

      {/* 输入框组件 */}
      {/* disabled: 加载中或未上传文档时禁用 */}
      <ChatInput onSend={handleSend} disabled={loading || !uploaded} />

      {/* 未上传文档提示 */}
      {!uploaded && (
        <p className="text-center text-gray-400 text-sm mt-2">
          请先上传 .txt 文档
        </p>
      )}
    </div>
  )
}

export default App
