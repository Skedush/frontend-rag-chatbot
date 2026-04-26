import axios from 'axios'

const API_BASE = '/api'

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

// 流式聊天，返回 ReadableStream
export function chatStream(question) {
  return fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  })
}

// 解析 SSE 流，返回 { content, sources }
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
    buffer = lines.pop() // 保留未完成的行

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
        } catch (e) {
          // ignore parse errors
        }
      }
    }
  }

  return { sources }
}

export async function getStats() {
  try {
    const response = await axios.get(`${API_BASE}/stats`)
    return response.data
  } catch {
    return { status: 'error' }
  }
}
