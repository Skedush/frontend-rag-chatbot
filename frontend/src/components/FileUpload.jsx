/**
 * 文件上传组件
 *
 * 功能：
 * 1. 上传 .txt 文档
 * 2. 调用后端 API 进行向量化
 * 3. 上传状态和错误提示
 */

import React, { useState } from 'react'
import { uploadFile } from '../api/chat'

/**
 * 文件上传组件
 *
 * @param {Function} onUploadSuccess - 上传成功回调
 */
export default function FileUpload({ onUploadSuccess }) {
  // 是否正在上传
  const [uploading, setUploading] = useState(false)

  // 状态消息（成功/失败提示）
  const [message, setMessage] = useState('')

  /**
   * 处理文件选择
   *
   * @param {Event} e - 文件 input 的 change 事件
   */
  const handleFileChange = async (e) => {
    const file = e.target.files[0]

    // 没有选择文件
    if (!file) return

    // 验证文件格式（只接受 .txt）
    if (!file.name.endsWith('.txt')) {
      setMessage('只支持 .txt 文件')
      return
    }

    setUploading(true)
    setMessage('上传中...')

    try {
      // 调用上传 API
      const result = await uploadFile(file)

      // 显示成功消息
      setMessage(result.message || '上传成功')

      // 调用成功回调
      // 让父组件更新 uploaded 状态，允许用户提问
      onUploadSuccess && onUploadSuccess()

    } catch (error) {
      // 处理错误
      const errorMsg = error.response?.data?.detail || error.message
      setMessage(`上传失败: ${errorMsg}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-4">
      <h3 className="font-medium mb-2">上传文档</h3>

      {/* 文件选择输入 */}
      <input
        type="file"
        accept=".txt"  // 只接受 .txt 文件
        onChange={handleFileChange}
        disabled={uploading}
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />

      {/* 状态消息 */}
      {message && (
        <p className={`mt-2 text-sm ${message.includes('失败') ? 'text-red-600' : 'text-green-600'}`}>
          {message}
        </p>
      )}
    </div>
  )
}
