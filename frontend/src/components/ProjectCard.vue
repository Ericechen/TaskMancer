<script setup lang="ts">
import { ref } from 'vue'
import { Project } from '../stores/projectStore'
import TaskTree from './TaskTree.vue'

defineProps<{
  project: Project
}>()

const isOpen = ref(false)
</script>

<template>
  <div class="bg-slate-800 rounded-xl p-4 shadow-lg border border-slate-700 flex flex-col h-full hover:border-sky-500 transition-colors duration-300">
    <!-- Header -->
    <div class="flex justify-between items-start mb-4">
      <div>
        <h3 class="text-lg font-bold text-white tracking-tight">{{ project.name }}</h3>
        <p class="text-xs text-slate-400 font-mono truncate max-w-[200px]" :title="project.path">
            {{ project.path }}
        </p>
      </div>
      <div 
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
