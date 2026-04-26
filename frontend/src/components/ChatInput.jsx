/**
 * 聊天输入框组件
 *
 * 功能：
 * 1. 文本输入框
 * 2. 发送按钮
 * 3. 禁用状态控制
 */

import React, { useState } from 'react'

/**
 * 聊天输入框组件
 *
 * @param {Function} onSend - 发送消息的回调函数
 * @param {Boolean} disabled - 是否禁用输入框
 */
export default function ChatInput({ onSend, disabled }) {
  // 输入框内容
  const [input, setInput] = useState('')

  /**
   * 处理表单提交
   *
   * @param {Event} e - 表单提交事件
   */
  const handleSubmit = (e) => {
    e.preventDefault()

    // 空内容或禁用状态时不发送
    if (!input.trim() || disabled) return

    // 调用父组件的发送函数
    onSend(input.trim())

    // 清空输入框
    setInput('')
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-4">
      <div className="flex gap-2">
        {/* 文本输入框 */}
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入你的问题..."
          disabled={disabled}  // 禁用状态（加载中或未上传文档时）
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        />

        {/* 发送按钮 */}
        <button
          type="submit"
          disabled={disabled || !input.trim()}  // 空内容时也禁用
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          发送
        </button>
      </div>
    </form>
  )
}
