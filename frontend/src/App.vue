<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useProjectStore } from './stores/projectStore'
import ProjectCard from './components/ProjectCard.vue'

const store = useProjectStore()
const showAddModal = ref(false)
const newProjectPath = ref('')
const isAdding = ref(false)

onMounted(() => {
  store.connect()
})

async function handleAddProject() {
  if (!newProjectPath.value) return
  
  isAdding.value = true
  const success = await store.addProject(newProjectPath.value)
  isAdding.value = false
  
  if (success) {
    showAddModal.value = false
    newProjectPath.value = ''
  } else {
    alert('Failed to add project. Please check if the path exists.')
  }
}
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

      <div class="flex items-center space-x-4">
        <!-- Add Project Button -->
        <button 
          @click="showAddModal = true"
          class="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors shadow-lg shadow-sky-900/20 flex items-center space-x-2"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Add Project</span>
        </button>

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
      </div>
    </header>

    <!-- Content -->
    <main class="max-w-7xl mx-auto">
      <!-- Empty State -->
      <div v-if="store.projects.length === 0 && store.isConnected" class="text-center py-20 text-slate-500">
         <p>No projects found with task.md</p>
         <p class="text-sm">Run with --root to scan a directory OR click "Add Project"</p>
      </div>

      <!-- Grid -->
      <div v-else class="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
        <div v-for="project in store.projects" :key="project.path" class="break-inside-avoid">
            <ProjectCard :project="project" />
        </div>
      </div>
    </main>

    <!-- Add Project Modal -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div class="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-700 shadow-2xl">
        <h3 class="text-lg font-bold text-white mb-4">Add Project Path</h3>
        <input 
          v-model="newProjectPath"
          type="text" 
          placeholder="e.g. D:\MyProjects\ProjectA"
          class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500 mb-4"
          @keyup.enter="handleAddProject"
        />
        <div class="flex justify-end space-x-2">
          <button 
            @click="showAddModal = false"
            class="px-4 py-2 rounded text-slate-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button 
            @click="handleAddProject"
            :disabled="isAdding || !newProjectPath"
            class="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ isAdding ? 'Adding...' : 'Add' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
