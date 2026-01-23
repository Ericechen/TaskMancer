<script setup lang="ts">
import { ref } from 'vue'
import { useProjectStore, type Project } from '../stores/projectStore'
import TaskTree from './TaskTree.vue'

defineProps<{
  project: Project
}>()

const store = useProjectStore()
const isOpen = ref(false)
const isDeleting = ref(false)

async function handleDelete(path: string) {
    if (!confirm(`Are you sure you want to stop monitoring this project?\n\n${path}`)) return
    
    isDeleting.value = true
    await store.removeProject(path)
    isDeleting.value = false
}
</script>

<template>
  <div class="bg-slate-800 rounded-xl p-4 shadow-lg border border-slate-700 flex flex-col h-full hover:border-sky-500 transition-colors duration-300 relative group">
    <!-- Delete Button (visible on hover) -->
    <button 
        @click="handleDelete(project.path)"
        :disabled="isDeleting"
        class="absolute top-2 right-2 p-1.5 rounded-lg bg-slate-700/80 text-rose-400 opacity-0 group-hover:opacity-100 transition-all hover:bg-slate-600 hover:text-rose-300 disabled:opacity-50 z-10"
        title="Remove Project"
    >
        <svg v-if="isDeleting" class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
             <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
             <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
    </button>

    <!-- Header -->
    <div class="flex justify-between items-start mb-4 pr-6">
      <div class="overflow-hidden">
        <h3 class="text-lg font-bold text-white tracking-tight truncate">{{ project.name }}</h3>
        <p class="text-xs text-slate-400 font-mono truncate" :title="project.path">
            {{ project.path }}
        </p>
      </div>
      <div 
        class="flex-shrink-0 ml-2"
        :class="[
          'px-2 py-0.5 rounded text-xs font-bold',
          project.stats.percentage === 100 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-sky-500/10 text-sky-400'
        ]"
      >
        {{ project.stats.percentage }}%
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="w-full bg-slate-700 rounded-full h-2 mb-4 overflow-hidden">
      <div 
        class="h-full rounded-full transition-all duration-500 ease-out"
        :class="project.stats.percentage === 100 ? 'bg-emerald-500' : 'bg-sky-500'"
        :style="{ width: `${project.stats.percentage}%` }"
      ></div>
    </div>

     <!-- Stats -->
    <div class="flex space-x-4 text-xs text-slate-400 mb-4">
       <span>Done: <strong class="text-slate-200">{{ project.stats.completed }}</strong></span>
       <span>Total: <strong class="text-slate-200">{{ project.stats.total }}</strong></span>
    </div>

    <!-- Expandable Task List -->
    <div class="mt-auto">
        <button 
            @click="isOpen = !isOpen"
            class="w-full py-2 px-3 rounded bg-slate-700 hover:bg-slate-600 text-xs text-slate-200 transition-colors flex items-center justify-center"
        >
            {{ isOpen ? 'Hide Tasks' : 'View Tasks' }}
        </button>
        
        <div v-if="isOpen" class="mt-4 pt-4 border-t border-slate-700 max-h-60 overflow-y-auto custom-scrollbar">
            <TaskTree :tasks="project.tasks" />
        </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}
</style>
