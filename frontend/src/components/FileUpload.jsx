import React, { useState } from 'react'
import { uploadFile } from '../api/chat'

export default function FileUpload({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.name.endsWith('.txt')) {
      setMessage('只支持 .txt 文件')
      return
    }

    setUploading(true)
    setMessage('上传中...')

    try {
      const result = await uploadFile(file)
      setMessage(result.message || '上传成功')
      onUploadSuccess && onUploadSuccess()
    } catch (error) {
      setMessage(`上传失败: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-4">
      <h3 className="font-medium mb-2">上传文档</h3>
      <input
        type="file"
        accept=".txt"
        onChange={handleFileChange}
        disabled={uploading}
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />
      {message && (
        <p className={`mt-2 text-sm ${message.includes('失败') ? 'text-red-600' : 'text-green-600'}`}>
          {message}
        </p>
      )}
    </div>
  )
}
