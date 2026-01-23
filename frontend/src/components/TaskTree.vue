<script setup lang="ts">
import { Task } from '../stores/projectStore'

defineProps<{
  tasks: Task[]
}>()
</script>

<template>
  <ul class="space-y-1">
    <li v-for="(task, index) in tasks" :key="index" class="relative">
      <div 
        class="flex items-start group"
      >
        <!-- Custom Checkbox Visual -->
        <div class="mt-1 mr-2 flex-shrink-0">
          <div v-if="task.status === 'done'" class="w-4 h-4 rounded bg-emerald-500 flex items-center justify-center">
             <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
             </svg>
          </div>
          <div v-else class="w-4 h-4 rounded border-2 border-slate-500 group-hover:border-slate-400"></div>
        </div>
        
        <!-- Text -->
        <span 
          :class="[
            'text-sm transition-colors duration-200',
            task.status === 'done' ? 'text-slate-500 line-through' : 'text-slate-200'
          ]"
        >
          {{ task.text }}
        </span>
      </div>

      <!-- Recursive Children -->
      <div v-if="task.children && task.children.length > 0" class="ml-4 pl-2 border-l border-slate-700 mt-1">
        <TaskTree :tasks="task.children" />
      </div>
    </li>
  </ul>
</template>
