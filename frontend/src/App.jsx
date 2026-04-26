import React, { useState, useEffect } from 'react'
import MessageList from './components/MessageList'
import FileUpload from './components/FileUpload'
import ChatInput from './components/ChatInput'
import { chatStream, parseStream, getStats } from './api/chat'

function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploaded, setUploaded] = useState(false)

  useEffect(() => {
    // 检查向量库是否已有数据
    getStats().then(result => {
      if (result.status === 'success') {
        setUploaded(true)
      }
    }).catch(() => {})
  }, [])

  const handleSend = async (question) => {
    // 添加用户消息
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const response = await chatStream(question)

      // 添加空的 AI 消息占位
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '',
          sources: [],
          isStreaming: true
        }
      ])

      let fullContent = ''
      let sources = []

      // 流式处理
      for await (const chunk of parseStream(response)) {
        if (chunk.content) {
          fullContent += chunk.content
          // 更新消息内容
          setMessages((prev) => {
            const newMsgs = [...prev]
            newMsgs[newMsgs.length - 1] = {
              ...newMsgs[newMsgs.length - 1],
              content: fullContent
            }
            return newMsgs
          })
        }
        if (chunk.sources && chunk.sources.length > 0) {
          sources = chunk.sources
        }
      }

      // 流结束，更新 sources
      setMessages((prev) => {
        const newMsgs = [...prev]
        newMsgs[newMsgs.length - 1] = {
          ...newMsgs[newMsgs.length - 1],
          isStreaming: false,
          sources: sources
        }
        return newMsgs
      })

    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `抱歉，发生错误: ${error.message}` }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = () => {
    setUploaded(true)
  }

  return (
    <div className="min-h-screen flex flex-col max-w-4xl mx-auto p-4">
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-center text-gray-800">
          Frontend RAG Chatbot
        </h1>
        <p className="text-center text-gray-500 text-sm mt-1">
          基于文档的智能问答系统
        </p>
      </header>

      <FileUpload onUploadSuccess={handleUploadSuccess} />

      <div className="flex-1 bg-gray-50 rounded-lg shadow-inner mb-4 overflow-hidden">
        <MessageList messages={messages} />
      </div>

      <ChatInput onSend={handleSend} disabled={loading || !uploaded} />

      {!uploaded && (
        <p className="text-center text-gray-400 text-sm mt-2">
          请先上传 .txt 文档
        </p>
      )}
    </div>
  )
}

export default App
