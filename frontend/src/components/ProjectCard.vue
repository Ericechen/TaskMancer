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
  <div class="bg-transparent border border-border p-5 flex flex-col h-full hover:border-accent/50 transition-colors duration-300 relative group rounded-xl">
    <!-- Delete Button (visible on hover) -->
    <button 
        @click="handleDelete(project.path)"
        :disabled="isDeleting"
        class="absolute top-4 right-4 text-border hover:text-danger opacity-0 group-hover:opacity-100 transition-all disabled:opacity-50 z-10"
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
    <div class="mb-6 pr-6">
      <div class="flex items-center space-x-2 mb-1">
          <div :class="['w-1.5 h-1.5 rounded-full', project.stats.percentage === 100 ? 'bg-success' : 'bg-accent']"></div>
          <h3 class="text-lg font-display font-medium text-primary tracking-tight truncate">{{ project.name }}</h3>
      </div>
      <p class="text-[10px] text-secondary font-mono truncate opacity-60 pl-3.5" :title="project.path">
          {{ project.path }}
      </p>
    </div>

    <!-- Stats Grid -->
    <div class="flex items-baseline space-x-6 text-sm mb-4 pl-3.5">
       <div class="flex flex-col">
           <span class="text-[10px] text-secondary uppercase tracking-widest font-bold">Progress</span>
           <span class="font-mono font-bold" :class="project.stats.percentage === 100 ? 'text-success' : 'text-primary'">{{ project.stats.percentage }}%</span>
       </div>
       <div class="flex flex-col">
           <span class="text-[10px] text-secondary uppercase tracking-widest font-bold">Done</span>
           <span class="font-mono text-secondary">{{ project.stats.completed }} / {{ project.stats.total }}</span>
       </div>
    </div>

    <!-- Progress Line -->
    <div class="w-full bg-border/30 h-[1px] mb-4 overflow-hidden relative">
      <div 
        class="h-[1px] absolute top-0 left-0 transition-all duration-500 ease-out"
        :class="project.stats.percentage === 100 ? 'bg-success' : 'bg-accent'"
        :style="{ width: `${project.stats.percentage}%` }"
      ></div>
    </div>

    <!-- Expandable Task List -->
    <div class="mt-auto">
        <button 
            @click="isOpen = !isOpen"
            class="w-full py-2 rounded-lg border border-transparent hover:border-border text-xs text-secondary hover:text-primary transition-all flex items-center justify-center space-x-1"
        >
            <span>{{ isOpen ? 'Collapse' : 'Inspect' }}</span>
            <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-180': isOpen }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
        </button>
        
        <div v-if="isOpen" class="mt-4 pt-2 border-t border-border/50 max-h-60 overflow-y-auto custom-scrollbar">
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
