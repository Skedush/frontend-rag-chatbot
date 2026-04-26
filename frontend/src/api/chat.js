/**
 * RAG Chatbot API 调用模块
 *
 * 功能：
 * 1. 文件上传
 * 2. 流式聊天
 * 3. SSE 流解析
 * 4. 健康检查
 */

import axios from 'axios'

// API 基础路径
// 开发环境通过 Vite 代理到后端
// 生产环境通过 Nginx 反向代理
const API_BASE = '/api'

/**
 * 上传文档
 *
 * @param {File} file - 要上传的文件对象
 * @returns {Promise} 返回上传结果
 *
 * 说明：
 * - 使用 FormData 格式（multipart/form-data）
 * - axios 会自动设置正确的 Content-Type
 */
export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * 发起流式聊天请求
 *
 * @param {string} question - 用户问题
 * @returns {Response} Fetch API 的 Response 对象，包含可读流
 *
 * 使用 Fetch API 而非 axios，因为：
 * - 需要处理流式响应（Response.body.getReader()）
 * - axios 不直接支持流式响应
 *
 * 返回的流格式：
 * - data: {"content": "字"}\n\n
 * - data: {"sources": [...]}\n\n
 * - data: [DONE]\n\n
 */
export function chatStream(question) {
  return fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  })
}

/**
 * 解析 SSE 流
 *
 * 这是一个异步生成器函数
 * 用于逐步解析服务器发送的 SSE 数据
 *
 * @param {Response} response - Fetch API 的响应对象
 * @yields {Object} 每个 chunk 包含：
 *   - content: 新生成的文字（如果有）
 *   - sources: 来源文档（如果有）
 *
 * @returns {AsyncGenerator} 生成器对象
 *
 * SSE 格式说明：
 * - 每个数据行格式：data: {...}\n\n
 * - 内容行：data: {"content": "字"}\n\n
 * - 来源行：data: {"sources": [...]}\n\n
 * - 结束行：data: [DONE]\n\n
 *
 * 使用方式：
 * for await (const chunk of parseStream(response)) {
 *   if (chunk.content) { // 处理新文字 }
 *   if (chunk.sources) { // 处理来源文档 }
 * }
 */
export async function* parseStream(response) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''      // 未处理完的字符缓冲
  let sources = []     // 累积来源文档

  while (true) {
    // 读取下一个数据块
    const { value, done } = await reader.read()

    // 流结束
    if (done) break

    // 解码数据块（stream: true 表示继续接收）
    buffer += decoder.decode(value, { stream: true })

    // 按行分割
    const lines = buffer.split('\n')

    // 最后一行可能不完整，保留在 buffer 中
    buffer = lines.pop()

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)  // 去掉 "data: " 前缀

        // 结束标记
        if (data === '[DONE]') {
          return { sources }
        }

        try {
          const parsed = JSON.parse(data)

          // 内容块
          if (parsed.content) {
            yield { content: parsed.content, sources: [] }
          }

          // 来源块（通常在流结束时发送）
          if (parsed.sources) {
            sources = parsed.sources
          }
        } catch (e) {
          // JSON 解析失败，忽略这行
        }
      }
    }
  }

  // 返回最终的 sources
  return { sources }
}

/**
 * 获取向量库状态
 *
 * 用于检查后端是否就绪
 *
 * @returns {Promise<Object>} { status: 'success' | 'error' }
 */
export async function getStats() {
  try {
    const response = await axios.get(`${API_BASE}/stats`)
    return response.data
  } catch {
    // 失败返回 error 状态
    return { status: 'error' }
  }
}
