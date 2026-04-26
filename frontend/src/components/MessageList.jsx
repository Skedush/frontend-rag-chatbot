import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function SourceDocuments({ sources }) {
  const [expanded, setExpanded] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-4 pt-3 border-t border-gray-200">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
      >
        <span>{expanded ? '▼' : '▶'}</span>
        <span>参考文档 ({sources.length})</span>
      </button>
      {expanded && (
        <div className="mt-3 space-y-2">
          {sources.map((doc, i) => (
            <div key={i} className="bg-gray-50 rounded-lg p-3 text-sm border border-gray-200">
              <div className="text-gray-500 mb-2 flex items-center gap-2">
                <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">📄</span>
                <span>{doc.metadata?.source || '未知来源'}</span>
              </div>
              <div className="text-gray-700 whitespace-pre-wrap">{doc.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ThinkingBlock({ content }) {
  const [expanded, setExpanded] = useState(false)

  if (!content) return null

  return (
    <div className="my-3 border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 bg-gray-100 text-gray-600 text-xs flex items-center justify-between hover:bg-gray-200 transition-colors"
      >
        <span className="flex items-center gap-2">
          <span>🤔</span>
          <span>思考过程</span>
        </span>
        <span>{expanded ? '▲ 收起' : '▼ 展开'}</span>
      </button>
      {expanded && (
        <div className="p-3 bg-gray-50 text-sm text-gray-600 whitespace-pre-wrap max-h-64 overflow-y-auto">
          {content}
        </div>
      )}
    </div>
  )
}

// 分离思考内容和实际内容
function parseContent(text) {
  if (!text) return { thinking: '', content: text }

  const thinkMatch = text.match(/<think>([\s\S]*?)<\/think>/)
  if (thinkMatch) {
    const thinking = thinkMatch[1].trim()
    const content = text.replace(/<think>[\s\S]*?<\/think>/, '').trim()
    return { thinking, content }
  }

  return { thinking: '', content: text }
}

export default function MessageList({ messages }) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-400 mt-20">
          <p className="text-lg">上传文档后，开始提问吧</p>
          <p className="text-sm mt-2">例如："React useState 怎么用？"</p>
        </div>
      )}
      {messages.map((msg, index) => {
        const { thinking, content } = parseContent(msg.content)

        return (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-xl p-4 shadow-sm ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <div className={`font-medium text-sm mb-3 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
                {msg.role === 'user' ? '你' : '🤖 AI 助手'}
              </div>
              {msg.role === 'user' ? (
                <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
              ) : (
                <>
                  {thinking && <ThinkingBlock content={thinking} />}
                  <div className="prose prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '')
                          if (!inline && match) {
                            return (
                              <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 my-3 overflow-x-auto text-sm">
                                <code className={`language-${match[1]}`} {...props}>
                                  {children}
                                </code>
                              </pre>
                            )
                          }
                          return (
                            <code className="bg-gray-100 text-pink-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                              {children}
                            </code>
                          )
                        },
                        p({ children }) {
                          return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
                        },
                        h1({ children }) {
                          return <h1 className="text-xl font-bold mt-4 mb-2 text-gray-900">{children}</h1>
                        },
                        h2({ children }) {
                          return <h2 className="text-lg font-bold mt-4 mb-2 text-gray-900">{children}</h2>
                        },
                        h3({ children }) {
                          return <h3 className="text-base font-bold mt-3 mb-2 text-gray-900">{children}</h3>
                        },
                        ul({ children }) {
                          return <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>
                        },
                        ol({ children }) {
                          return <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>
                        },
                        li({ children }) {
                          return <li className="text-gray-700">{children}</li>
                        },
                        strong({ children }) {
                          return <strong className="font-semibold">{children}</strong>
                        },
                        em({ children }) {
                          return <em className="italic">{children}</em>
                        },
                        blockquote({ children }) {
                          return <blockquote className="border-l-4 border-blue-500 pl-4 my-2 text-gray-600 italic">{children}</blockquote>
                        }
                      }}
                    >
                      {content}
                    </ReactMarkdown>
                    {msg.isStreaming && <span className="animate-pulse">▍</span>}
                  </div>
                  <SourceDocuments sources={msg.sources} />
                </>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
