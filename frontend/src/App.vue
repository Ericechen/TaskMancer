<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useProjectStore } from './stores/projectStore'
import ProjectCard from './components/ProjectCard.vue'

const store = useProjectStore()
const showAddModal = ref(false)

// Discovery Logic
const modalStep = ref<'input' | 'results'>('input')
const discoveryPath = ref('')
const isScanning = ref(false)
const isImporting = ref(false)
const discoveredProjects = ref<{name: string, path: string}[]>([])
const selectedPaths = ref<Set<string>>(new Set())

onMounted(() => {
  store.connect()
  store.fetchConfig()
})

function openModal() {
  showAddModal.value = true
  modalStep.value = 'input'
  discoveryPath.value = store.discoveryRoot
  discoveredProjects.value = []
  selectedPaths.value.clear()
}

async function handleScan() {
  if (!discoveryPath.value) return
  
  isScanning.value = true
  const results = await store.discoverProjects(discoveryPath.value)
  isScanning.value = false
  
  if (results.length === 0) {
    alert('No "task.md" projects found in immediate subdirectories.')
    return
  }

  discoveredProjects.value = results
  
  // Auto-select only new projects
  const existingPaths = new Set(store.projects.map((p: { path: string }) => p.path))
  results.forEach((p: { path: string }) => {
    if (!existingPaths.has(p.path)) {
      selectedPaths.value.add(p.path)
    }
  })
  
  modalStep.value = 'results'
}

function toggleSelection(path: string) {
  if (selectedPaths.value.has(path)) {
    selectedPaths.value.delete(path)
  } else {
    selectedPaths.value.add(path)
  }
}

async function handleImport() {
  if (selectedPaths.value.size === 0) return

  isImporting.value = true
  
  // Parallel import?
  const promises = Array.from(selectedPaths.value).map(path => store.addProject(path))
  await Promise.all(promises)
  
  isImporting.value = false
  showAddModal.value = false
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
          @click="openModal"
          class="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors shadow-lg shadow-sky-900/20 flex items-center space-x-2"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Add Projects</span>
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
         <p class="text-lg mb-2">No projects monitored yet.</p>
         <p class="text-sm">Click "Add Projects" to scan and import your task projects.</p>
      </div>

      <!-- Grid -->
      <div v-else class="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
        <div v-for="project in store.projects" :key="project.path" class="break-inside-avoid">
            <ProjectCard :project="project" />
        </div>
      </div>
    </main>

    <!-- Discovery Modal -->
    <div v-if="showAddModal" @click.self="showAddModal = false" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div class="bg-slate-800 rounded-xl p-6 w-full max-w-lg border border-slate-700 shadow-2xl flex flex-col max-h-[80vh]">
        <div class="mb-4">
            <h3 class="text-lg font-bold text-white">
                {{ modalStep === 'input' ? 'Discover Projects' : 'Select Projects to Import' }}
            </h3>
            <p v-if="modalStep === 'input'" class="text-xs text-slate-400 mt-1">
                Enter a root directory to scan for 'task.md' files.
            </p>
        </div>

        <!-- Step 1: Input -->
        <div v-if="modalStep === 'input'" class="flex flex-col space-y-4">
            <div>
                <label class="block text-xs font-medium text-slate-300 mb-1">Discovery Root</label>
                <input 
                  v-model="discoveryPath"
                  type="text" 
                  placeholder="e.g. D:\Dev"
                  class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                  @keyup.enter="handleScan"
                />
            </div>
            <div class="bg-slate-900/50 p-3 rounded text-xs text-slate-400 border border-slate-700/50">
                <span class="font-bold text-sky-400">Note:</span> Only immediate subdirectories containing <code>task.md</code> will be found.
            </div>
        </div>

        <!-- Step 2: Results -->
        <div v-else class="flex-1 overflow-y-auto min-h-0 space-y-2 pr-2 mb-4 custom-scrollbar">
             <div 
                v-for="proj in discoveredProjects" 
                :key="proj.path"
                class="flex items-center p-3 rounded-lg border transition-colors"
                :class="[
                    store.projects.some(p => p.path === proj.path) 
                        ? 'bg-slate-800/50 border-slate-800 opacity-50 cursor-not-allowed' 
                        : (selectedPaths.has(proj.path) ? 'bg-sky-900/20 border-sky-500/50 cursor-pointer' : 'bg-slate-900/50 border-slate-700 hover:border-slate-600 cursor-pointer')
                ]"
                @click="!store.projects.some(p => p.path === proj.path) && toggleSelection(proj.path)"
             >
                <div class="flex-shrink-0 mr-3">
                    <div 
                        v-if="!store.projects.some(p => p.path === proj.path)"
                        class="w-5 h-5 rounded border flex items-center justify-center transition-colors"
                        :class="selectedPaths.has(proj.path) ? 'bg-sky-500 border-sky-500' : 'border-slate-600'"
                    >
                        <svg v-if="selectedPaths.has(proj.path)" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                     <div 
                        v-else
                        class="w-5 h-5 rounded border border-slate-700 bg-slate-800 flex items-center justify-center"
                    >
                        <svg class="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                </div>
                <div class="min-w-0">
                    <div class="font-medium text-slate-200 truncate">{{ proj.name }}</div>
                    <div class="text-xs text-slate-500 truncate">{{ proj.path }}</div>
                </div>
                <div v-if="store.projects.some(p => p.path === proj.path)" class="ml-auto text-xs text-slate-500 font-medium px-2 py-0.5 border border-slate-700 rounded">
                    Added
                </div>
             </div>
        </div>

        <!-- Footer Buttons -->
        <div class="flex justify-end space-x-2 mt-4 pt-4 border-t border-slate-700">
          <button 
            @click="showAddModal = false"
            class="px-4 py-2 rounded text-slate-400 hover:text-white transition-colors text-sm"
          >
            Cancel
          </button>
          
          <button 
            v-if="modalStep === 'input'"
            @click="handleScan"
            :disabled="isScanning || !discoveryPath"
            class="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center space-x-2"
          >
            <svg v-if="isScanning" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isScanning ? 'Scanning...' : 'Scan' }}</span>
          </button>

          <div v-else class="flex space-x-2">
             <button 
                @click="modalStep = 'input'"
                class="px-4 py-2 rounded text-slate-300 hover:bg-slate-700 transition-colors text-sm"
              >
                Back
             </button>
             <button 
                @click="handleImport"
                :disabled="isImporting || selectedPaths.size === 0"
                class="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center space-x-2"
              >
                <svg v-if="isImporting" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ isImporting ? 'Importing...' : `Import (${selectedPaths.size})` }}</span>
              </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
