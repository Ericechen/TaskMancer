<script setup lang="ts">
import { onMounted } from 'vue'
import { useProjectStore } from './stores/projectStore'
import ProjectCard from './components/ProjectCard.vue'

const store = useProjectStore()

onMounted(() => {
  store.connect()
})
</script>

<template>
  <div class="min-h-screen bg-slate-900 text-slate-50 p-6 font-sans">
    <!-- Header -->
    <header class="flex justify-between items-center mb-10 max-w-7xl mx-auto">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-gradient-to-br from-sky-500 to-indigo-600 rounded-lg shadow-lg shadow-sky-500/20 flex items-center justify-center text-xl font-bold">
            TM
        </div>
        <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-indigo-400">
            TaskMancer
        </h1>
      </div>

      <!-- Connection Status -->
      <div class="flex items-center space-x-2 bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700">
        <span class="relative flex h-2.5 w-2.5">
          <span 
            v-if="store.isConnected"
            class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"
          ></span>
          <span 
            :class="store.isConnected ? 'bg-emerald-500' : 'bg-rose-500'"
            class="relative inline-flex rounded-full h-2.5 w-2.5"
          ></span>
        </span>
        <span class="text-xs font-medium text-slate-300">
            {{ store.isConnected ? 'Live' : 'Disconnected' }}
        </span>
      </div>
    </header>

    <!-- Content -->
    <main class="max-w-7xl mx-auto">
      <!-- Empty State -->
      <div v-if="store.projects.length === 0 && store.isConnected" class="text-center py-20 text-slate-500">
         <p>No projects found with task.md</p>
         <p class="text-sm">Run with --root to scan a directory</p>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ProjectCard 
            v-for="project in store.projects" 
            :key="project.path" 
            :project="project" 
        />
      </div>
    </main>
  </div>
</template>
