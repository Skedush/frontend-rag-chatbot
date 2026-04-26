<template>
  <div class="mb-4">
    <el-upload
      ref="uploadRef"
      drag
      :auto-upload="false"
      :limit="1"
      accept=".txt"
      :on-change="handleFileChange"
      :on-remove="handleRemove"
      :file-list="fileList"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">支持 .txt 文件</div>
      </template>
    </el-upload>

    <div class="mt-3 flex gap-2">
      <el-button
        type="success"
        :disabled="!selectedFile || isUploading"
        @click="handleUpload"
      >
        <el-icon class="mr-1" v-if="isUploading"><Loading /></el-icon>
        {{ isUploading ? '上传中...' : '开始上传' }}
      </el-button>
    </div>

    <el-alert
      v-if="message"
      :title="message"
      :type="messageType === 'error' ? 'error' : 'success'"
      :closable="true"
      show-icon
      class="mt-3"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadFile } from '../api/chat'
import { UploadFilled, Loading } from '@element-plus/icons-vue'

const emit = defineEmits(['uploaded'])

const uploadRef = ref(null)
const selectedFile = ref(null)
const fileList = ref([])
const isUploading = ref(false)
const message = ref('')
const messageType = ref('')

function handleFileChange(file, files) {
  fileList.value = files.slice(-1)
  selectedFile.value = file.raw
  message.value = ''
}

function handleRemove() {
  selectedFile.value = null
  fileList.value = []
}

async function handleUpload() {
  if (!selectedFile.value || isUploading.value) return

  isUploading.value = true
  message.value = ''

  try {
    const result = await uploadFile(selectedFile.value)
    message.value = `上传成功！已处理 ${result.chunks} 个文本块`
    messageType.value = 'success'
    selectedFile.value = null
    fileList.value = []
    emit('uploaded', result)
  } catch (error) {
    message.value = `上传失败：${error.message}`
    messageType.value = 'error'
  } finally {
    isUploading.value = false
  }
}
</script>
