/**
 * API 服务层
 *
 * 封装所有与后端的 HTTP 通信
 * 使用 Fetch API 实现流式请求
 */

const API_BASE = '/api'

/**
 * 上传文档
 * @param {File} file - 文件对象
 * @returns {Promise<Object>} 上传结果
 */
export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Upload failed')
  }

  return response.json()
}

/**
 * 获取向量库状态
 * @returns {Promise<Object>} 状态信息
 */
export async function getStats() {
  try {
    const response = await fetch(`${API_BASE}/stats`)
    return response.json()
  } catch {
    return { status: 'error' }
  }
}

/**
 * 发送聊天消息（流式）
 * @param {string} question - 用户问题
 * @returns {Response} Fetch Response 对象，包含可读流
 */
export function chatStream(question) {
  return fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ question })
  })
}

/**
 * 解析 SSE 流
 * @param {Response} response - Fetch Response 对象
 * @yields {Object} { content, sources }
 */
export async function* parseStream(response) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let sources = []

  while (true) {
    const { value, done } = await reader.read()

    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)

        if (data === '[DONE]') {
          return { sources }
        }

        try {
          const parsed = JSON.parse(data)

          if (parsed.content) {
            yield { content: parsed.content, sources: [] }
          }

          if (parsed.sources) {
            sources = parsed.sources
          }
        } catch {
          // ignore parse error
        }
      }
    }
  }

  return { sources }
}
