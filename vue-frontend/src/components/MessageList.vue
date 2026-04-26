<template>
  <div class="flex-1 overflow-y-auto space-y-4">
    <div v-if="messages.length === 0" class="text-center text-gray-400 mt-8">
      <el-empty description="开始对话吧！" :image-size="80" />
    </div>

    <div v-for="(msg, index) in messages" :key="index" class="mb-4">
      <!-- 用户消息 -->
      <div v-if="msg.role === 'user'" class="flex justify-end">
        <el-card class="max-w-[80%] bg-blue-500 border-blue-500" body-style="padding: 12px 16px;">
          <span class="text-white">{{ msg.content }}</span>
        </el-card>
      </div>

      <!-- 助手消息 -->
      <div v-else class="flex justify-start">
        <el-card class="max-w-[80%]" body-style="padding: 12px 16px;">
          <div class="markdown-body" v-html="renderedContent(msg.content)"></div>

          <!-- 参考文档 -->
          <div v-if="index === messages.length - 1 && sources.length > 0" class="mt-3 pt-2 border-t border-gray-200">
            <el-divider content-position="left">
              <span class="text-xs text-gray-500">参考文档</span>
            </el-divider>
            <ul class="text-xs text-gray-600 space-y-1">
              <li v-for="(source, i) in sources" :key="i" class="truncate">
                <el-tag size="small" type="info" class="mr-1">#{{ i + 1 }}</el-tag>
                {{ source.metadata?.source || source.page_content?.substring(0, 50) + '...' }}
              </li>
            </ul>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 流式输出指示器 -->
    <div v-if="isStreaming" class="flex justify-start">
      <el-card class="max-w-[80%]" body-style="padding: 12px 16px;">
        <el-icon class="is-loading"><Loading /></el-icon>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'
import hljs from 'highlight.js'
import { Loading } from '@element-plus/icons-vue'

marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return code
  }
})

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  sources: {
    type: Array,
    default: () => []
  },
  isStreaming: {
    type: Boolean,
    default: false
  }
})

function renderedContent(content) {
  if (!content) return ''
  return marked.parse(content)
}
</script>
