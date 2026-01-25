<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()
const isRunning = ref(false)
const isLoading = ref(false)

async function checkStatus() {
    isRunning.value = await invoke('get_backend_status')
}

async function toggleService() {
    isLoading.value = true
    if (isRunning.value) {
        await invoke('stop_backend')
    } else {
        await invoke('start_backend')
    }
    await checkStatus()
    isLoading.value = false
}

let interval: any
onMounted(() => {
    checkStatus()
    interval = setInterval(checkStatus, 3000)
    store.fetchConfig()
})

onUnmounted(() => {
    clearInterval(interval)
})
</script>

<template>
  <div class="tray-container p-4 bg-void border border-border rounded-xl shadow-2xl h-screen overflow-hidden flex flex-col">
    <div class="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
        <div class="flex items-center space-x-2">
            <div class="w-2 h-2 rounded-full" :class="isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'"></div>
            <span class="text-xs font-bold uppercase tracking-widest text-secondary">
                {{ isRunning ? 'Service Active' : 'Service Stopped' }}
            </span>
        </div>
        <div class="text-[10px] font-mono opacity-40">v1.2.0</div>
    </div>

    <div class="flex-1 flex flex-col justify-center items-center space-y-6">
        <button 
            @click="toggleService"
            :disabled="isLoading"
            class="w-24 h-24 rounded-full border-2 flex items-center justify-center transition-all duration-500 group relative"
            :class="isRunning ? 'border-emerald-500/50 hover:bg-emerald-500/10' : 'border-accent/50 hover:bg-accent/10'"
        >
            <div class="absolute inset-0 rounded-full animate-ping opacity-20" :class="isRunning ? 'bg-emerald-500' : 'bg-accent'" v-if="isLoading"></div>
            
            <svg v-if="!isRunning" class="w-10 h-10 text-accent group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
            </svg>
            <svg v-else class="w-10 h-10 text-emerald-500 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
            </svg>
        </button>
        
        <div class="text-center">
            <h2 class="text-lg font-display font-bold text-primary mb-1">TaskMancer</h2>
            <p class="text-[10px] text-secondary">Click to {{ isRunning ? 'stop' : 'start' }} orchestrator</p>
        </div>
    </div>

    <div class="mt-4 pt-4 border-t border-white/5 flex flex-col space-y-2">
        <button 
            class="w-full py-2 bg-surface hover:bg-white/10 text-xs font-bold text-primary rounded-lg transition-colors border border-border"
            @click="invoke('show_main_window')"
        >
            Open Dashboard
        </button>
    </div>
  </div>
</template>

<style scoped>
.tray-container {
    background: radial-gradient(circle at top right, rgba(124, 92, 255, 0.05), transparent), #0a0a0c;
}
</style>
