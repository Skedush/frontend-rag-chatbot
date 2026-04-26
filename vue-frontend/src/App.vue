<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm py-4">
      <h1 class="text-2xl font-bold text-center text-gray-800">
        Vue RAG Chatbot
      </h1>
      <p class="text-center text-gray-500 text-sm">
        基于文档的智能问答系统 (Vue 3.0 + Element Plus)
      </p>
    </header>

    <main class="max-w-4xl mx-auto p-4">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>
