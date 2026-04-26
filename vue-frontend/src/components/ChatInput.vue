<template>
  <div class="mt-4">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      placeholder="输入你的问题..."
      :disabled="disabled"
      @keyup.enter.exact.prevent="handleSend"
      @pressEnter="handleSend"
    >
      <template #append>
        <el-button
          type="primary"
          :disabled="disabled || !inputText.trim()"
          @click="handleSend"
        >
          <el-icon class="mr-1"><Promotion /></el-icon>
          发送
        </el-button>
      </template>
    </el-input>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])

const inputText = ref('')

function handleSend() {
  const text = inputText.value.trim()
  if (text && !props.disabled) {
    emit('send', text)
    inputText.value = ''
  }
}
</script>
