<template>
  <div class="flex flex-col h-[calc(100vh-120px)]">
    <!-- 消息列表 -->
    <MessageList
      :messages="messages"
      :sources="sources"
      :is-streaming="isStreaming"
    />

    <!-- 文件上传 -->
    <FileUpload @uploaded="handleUploaded" />

    <!-- 聊天输入 -->
    <ChatInput :disabled="isStreaming" @send="handleSend" />

    <!-- 清空按钮 -->
    <div class="mt-2 text-center">
      <el-button
        v-if="messages.length > 0"
        text
        type="info"
        @click="handleClear"
      >
        清空对话
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '../stores/chat'
import MessageList from '../components/MessageList.vue'
import ChatInput from '../components/ChatInput.vue'
import FileUpload from '../components/FileUpload.vue'

const chatStore = useChatStore()

const messages = computed(() => chatStore.messages)
const sources = computed(() => chatStore.sources)
const isStreaming = computed(() => chatStore.isStreaming)

function handleSend(question) {
  chatStore.sendMessage(question)
}

function handleClear() {
  chatStore.clearMessages()
}

function handleUploaded(result) {
  console.log('Document uploaded:', result)
}
</script>
