<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useProjectStore } from './stores/projectStore'
import ProjectList from './components/ProjectList.vue'
import DashboardView from './components/DashboardView.vue'
import { $swal, Toast } from './utils/swal'

const store = useProjectStore()
const showAddModal = ref(false)
const currentView = ref<'dashboard' | 'projects'>('dashboard')

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
  // Reset states
  modalStep.value = 'input'
  modalTab.value = 'scan'
  
  // Set defaults
  discoveryPath.value = store.discoveryRoot
  createForm.value = { 
      name: '', 
      parentPath: store.discoveryRoot || 'C:\\', // Fallback or empty
      file: null 
  }
  
  discoveredProjects.value = []
  selectedPaths.value.clear()
}

async function handleScan() {
  if (!discoveryPath.value) return
  
  isScanning.value = true
  const results = await store.discoverProjects(discoveryPath.value)
  isScanning.value = false
  
  if (results.length === 0) {
    $swal.fire({
        icon: 'info',
        title: 'No Projects Found',
        html: `
            <div class="text-sm text-secondary mb-4">We couldn't find any <code>task.md</code> files in the immediate subdirectories of:</div>
            <div class="bg-black/20 p-3 rounded border border-white/5 font-mono text-[10px] break-all opacity-70">${discoveryPath.value}</div>
        `
    })
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
  
  // Parallel import
  const promises = Array.from(selectedPaths.value).map(path => store.addProject(path))
  await Promise.all(promises)
  
  isImporting.value = false
  showAddModal.value = false
  
  Toast.fire({
      icon: 'success',
      title: `${selectedPaths.value.size} projects imported`
  })
}

// Create Logic
const modalTab = ref<'scan' | 'create'>('scan')
const createForm = ref({
    name: '',
    parentPath: '',
    file: null as File | null
})
const isCreating = ref(false)

function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement
    if (target.files && target.files.length > 0) {
        createForm.value.file = target.files[0] || null
    }
}

async function handleCreate() {
    if (!createForm.value.name || !createForm.value.parentPath) return

    isCreating.value = true
    try {
        await store.createProject(
            createForm.value.parentPath,
            createForm.value.name,
            createForm.value.file || null
        )
        // Success
        showAddModal.value = false
        // Reset form
        createForm.value = { name: '', parentPath: store.discoveryRoot, file: null }
        
        Toast.fire({
            icon: 'success',
            title: 'Project created successfully'
        })
    } catch (e: any) {
        $swal.fire({
            icon: 'error',
            title: 'Creation Failed',
            html: `
                <div class="text-sm text-danger/80 mb-4 font-bold">Unable to initialize the project directory.</div>
                <div class="bg-rose-500/10 p-3 rounded border border-rose-500/20 font-mono text-[10px] break-all text-rose-200 opacity-80">${e.message || 'Unknown filesystem error'}</div>
            `
        })
    } finally {
        isCreating.value = false
    }
}
</script>

<template>
  <div class="min-h-screen p-8 md:p-12 font-sans selection:bg-accent/30">
    <!-- Header -->
    <header class="flex flex-col md:flex-row justify-between items-end mb-16 max-w-7xl mx-auto gap-6 border-b border-border pb-6 animate-fade-in-up">
      <div class="flex items-center space-x-4 self-start md:self-auto group cursor-default">
        <div class="w-12 h-12 bg-surface border border-border rounded-xl flex items-center justify-center text-2xl font-bold text-accent shadow-2xl shadow-accent/5 group-hover:shadow-accent/20 transition-all duration-500">
            TM
        </div>
        <div>
            <h1 class="text-3xl font-display font-bold text-primary tracking-tighter group-hover:text-accent transition-colors duration-300">
                TaskMancer
            </h1>
            <p class="text-xs text-secondary font-mono mt-1 tracking-widest uppercase">Project Intelligence_v4.7.0</p>
        </div>
      </div>

      <!-- Navigation Tabs (Segmented Control) -->
      <div class="bg-surface p-1 rounded-lg flex space-x-1 border border-border">
          <button 
            @click="currentView = 'dashboard'"
            :class="currentView === 'dashboard' ? 'bg-void text-primary shadow-sm border border-border/50' : 'text-secondary hover:text-primary'"
            class="px-6 py-2 rounded-md text-sm font-medium transition-all duration-300"
          >
            Dashboard
          </button>
          <button 
             @click="currentView = 'projects'"
            :class="currentView === 'projects' ? 'bg-void text-primary shadow-sm border border-border/50' : 'text-secondary hover:text-primary'"
            class="px-6 py-2 rounded-md text-sm font-medium transition-all duration-300"
          >
            Projects
          </button>
      </div>

      <div class="flex items-center space-x-6 self-end md:self-auto">
        <!-- Add Project Button -->
        <button 
          @click="openModal"
          class="group flex items-center space-x-2 text-sm font-medium text-secondary hover:text-accent transition-colors"
        >
          <div class="w-8 h-8 rounded-full border border-dashed border-secondary flex items-center justify-center group-hover:border-accent group-hover:bg-accent/10 transition-all">
             <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
             </svg>
          </div>
          <span>Add Source</span>
        </button>

        <!-- Connection Status -->
        <div class="flex items-center space-x-2">
          <span class="relative flex h-2 w-2">
            <span 
              v-if="store.isConnected"
              class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"
            ></span>
            <span 
              :class="store.isConnected ? 'bg-emerald-500' : 'bg-rose-500'"
              class="relative inline-flex rounded-full h-2 w-2"
            ></span>
          </span>
          <span class="text-[10px] uppercase tracking-widest font-bold text-secondary">
              {{ store.isConnected ? 'Online' : 'Offline' }}
          </span>
        </div>
      </div>
    </header>

    <!-- Content -->
    <main class="max-w-7xl mx-auto animate-fade-in-up" style="animation-delay: 100ms;">
        <transition name="fade" mode="out-in">
             <KeepAlive>
                <component :is="currentView === 'dashboard' ? DashboardView : ProjectList" />
             </KeepAlive>
        </transition>
    </main>

    <!-- Discovery Modal -->
    <div v-if="showAddModal" @click.self="showAddModal = false" class="fixed inset-0 bg-void/80 backdrop-blur-md flex items-center justify-center p-4 z-50">
      <div class="bg-surface border border-border rounded-2xl p-8 w-full max-w-xl shadow-2xl relative overflow-hidden animate-subtle-scale">
         <!-- Decorative Noise/Glow -->
         <div class="absolute top-0 right-0 w-64 h-64 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

        <div class="mb-8 relative z-10">
            <!-- Modal Tabs -->
            <div class="flex space-x-6 border-b border-border/50 mb-6 pb-2">
                <button 
                    @click="modalTab = 'scan'"
                    class="text-sm font-display font-bold pb-2 border-b-2 transition-all"
                    :class="modalTab === 'scan' ? 'text-accent border-accent' : 'text-secondary border-transparent hover:text-primary'"
                >
                    Scan Existing
                </button>
                <button 
                    @click="modalTab = 'create'"
                    class="text-sm font-display font-bold pb-2 border-b-2 transition-all"
                    :class="modalTab === 'create' ? 'text-accent border-accent' : 'text-secondary border-transparent hover:text-primary'"
                >
                    Create New
                </button>
            </div>

            <h3 class="text-2xl font-display font-bold text-primary mb-2">
                {{ modalTab === 'scan' ? (modalStep === 'input' ? 'Initialize Discovery' : 'Select Sources') : 'New Project' }}
            </h3>
            <p class="text-sm text-secondary">
                {{ modalTab === 'scan' 
                    ? 'Enter a root directory path to recursively scan for task.md contexts.' 
                    : 'Initialize a new project folder with a task.md file.' 
                }}
            </p>
        </div>


        <!-- Tab Content: Scan Input -->
        <div v-if="modalTab === 'scan' && modalStep === 'input'" class="flex flex-col space-y-6 relative z-10 transition-all">
            <div>
                <label class="block text-xs font-bold text-secondary uppercase tracking-widest mb-3">Root Path</label>
                <input 
                  v-model="discoveryPath"
                  type="text" 
                  placeholder="D:\Development\Projects"
                  class="w-full bg-void border border-border rounded-lg px-5 py-3 text-primary placeholder-zinc-700 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all font-mono text-sm"
                  @keyup.enter="handleScan"
                />
            </div>
        </div>

        <!-- Tab Content: Scan Results -->
        <div v-else-if="modalTab === 'scan' && modalStep === 'results'" class="flex-1 overflow-y-auto min-h-0 space-y-2 pr-2 mb-8 custom-scrollbar max-h-[50vh] relative z-10">
             <!-- ... existing results list ... -->
             <div 
                v-for="proj in discoveredProjects" 
                :key="proj.path"
                class="flex items-center p-4 rounded-lg border transition-all duration-200 group"
                :class="[
                    store.projects.some(p => p.path === proj.path) 
                        ? 'bg-void/50 border-transparent opacity-40 cursor-not-allowed' 
                        : (selectedPaths.has(proj.path) ? 'bg-accent/10 border-accent/50 cursor-pointer' : 'bg-void border-border hover:border-zinc-600 cursor-pointer')
                ]"
                @click="!store.projects.some(p => p.path === proj.path) && toggleSelection(proj.path)"
             >
                <div class="flex-shrink-0 mr-4">
                    <div 
                        v-if="!store.projects.some(p => p.path === proj.path)"
                        class="w-5 h-5 rounded border flex items-center justify-center transition-colors"
                        :class="selectedPaths.has(proj.path) ? 'bg-accent border-accent' : 'border-zinc-700 group-hover:border-zinc-500'"
                    >
                        <svg v-if="selectedPaths.has(proj.path)" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                     <div 
                        v-else
                        class="w-5 h-5 flex items-center justify-center"
                    >
                        <svg class="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                </div>
                <div class="min-w-0 flex-1">
                    <div class="font-bold text-primary text-sm">{{ proj.name }}</div>
                    <div class="text-xs text-secondary font-mono truncate opacity-60">{{ proj.path }}</div>
                </div>
                <div v-if="store.projects.some(p => p.path === proj.path)" class="ml-auto text-[10px] uppercase font-bold text-secondary tracking-wider">
                    Linked
                </div>
             </div>
        </div>

        <!-- Tab Content: Create New -->
        <div v-else-if="modalTab === 'create'" class="flex flex-col space-y-6 relative z-10">
            <div>
                <label class="block text-xs font-bold text-secondary uppercase tracking-widest mb-3">Project Directory Name</label>
                <input 
                  v-model="createForm.name"
                  type="text" 
                  placeholder="MyNewProject"
                  class="w-full bg-void border border-border rounded-lg px-5 py-3 text-primary placeholder-zinc-700 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all font-sans text-sm font-bold"
                />
            </div>
            <div>
                <label class="block text-xs font-bold text-secondary uppercase tracking-widest mb-3">Parent Location</label>
                <input 
                  v-model="createForm.parentPath"
                  type="text" 
                  placeholder="D:\Development\Projects"
                  class="w-full bg-void border border-border rounded-lg px-5 py-3 text-primary placeholder-zinc-700 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all font-mono text-sm opacity-80 hover:opacity-100"
                />
                <p class="text-[10px] text-secondary mt-2">Folder will be created at: <span class="font-mono text-accent">{{ createForm.parentPath || '...' }}\{{ createForm.name || '...' }}</span></p>
            </div>
             <div>
                <label class="block text-xs font-bold text-secondary uppercase tracking-widest mb-3">Task File (task.md) <span class="text-[10px] opacity-50 ml-1 normal-case tracking-normal">(Optional - Auto-generated if empty)</span></label>
                <div class="relative group">
                    <input 
                        type="file" 
                        accept=".md"
                        @change="handleFileSelect"
                        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    />
                    <div class="w-full bg-void border border-dashed border-border rounded-lg px-5 py-4 flex items-center justify-center space-x-3 group-hover:border-accent/50 transition-colors">
                        <svg class="w-5 h-5 text-secondary group-hover:text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <span class="text-sm font-mono" :class="createForm.file ? 'text-primary' : 'text-zinc-600'">
                            {{ createForm.file ? createForm.file.name : 'Upload task.md...' }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer Buttons -->
        <div class="flex justify-end space-x-4 mt-8 pt-6 border-t border-border relative z-10">
          <button 
            @click="showAddModal = false"
            class="px-6 py-2.5 rounded-lg text-secondary hover:text-primary transition-colors text-sm font-medium"
          >
            Cancel
          </button>
          
          <!-- Scan Button -->
          <button 
            v-if="modalTab === 'scan' && modalStep === 'input'"
            @click="handleScan"
            :disabled="isScanning || !discoveryPath"
            class="px-6 py-2.5 rounded-lg bg-primary hover:bg-white text-void disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-bold flex items-center space-x-2 shadow-lg shadow-white/5"
          >
            <svg v-if="isScanning" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isScanning ? 'Scanning...' : 'Scan Directory' }}</span>
          </button>
          
          <!-- Create Button -->
           <button 
            v-else-if="modalTab === 'create'"
            @click="handleCreate"
            :disabled="isCreating || !createForm.name || !createForm.parentPath"
            class="px-6 py-2.5 rounded-lg bg-accent hover:bg-accent/90 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-bold flex items-center space-x-2 shadow-lg shadow-accent/20"
          >
            <svg v-if="isCreating" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isCreating ? 'Creating...' : 'Create Project' }}</span>
          </button>

          <!-- Import Button (Scan Results) -->
          <div v-else class="flex space-x-3">
             <button 
                @click="modalStep = 'input'"
                class="px-6 py-2.5 rounded-lg text-secondary hover:bg-void transition-colors text-sm font-medium border border-transparent hover:border-border"
              >
                Back
             </button>
             <button 
                @click="handleImport"
                :disabled="isImporting || selectedPaths.size === 0"
                class="px-6 py-2.5 rounded-lg bg-accent hover:bg-accent/90 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-bold flex items-center space-x-2 shadow-lg shadow-accent/20"
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

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(5px);
}
</style>
