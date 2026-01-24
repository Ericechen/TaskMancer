<script setup lang="ts">
import { computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import ProjectCard from './ProjectCard.vue'
import ProcessDashboard from './ProcessDashboard.vue'
import MonitorTile from './MonitorTile.vue'

const store = useProjectStore()

function getLatestLogs(path: string) {
    const logs = store.projectLogs[path] || []
    return logs.slice(-50)
}

const layoutMode = computed(() => store.layoutMode)

// [v11.0] Multi-criteria Filtering
const filteredProjects = computed(() => {
    let results = store.projects
    
    // 1. Search Query
    if (store.searchQuery) {
        const query = store.searchQuery.toLowerCase()
        results = results.filter(p => 
            p.name.toLowerCase().includes(query) || 
            p.path.toLowerCase().includes(query)
        )
    }

    // 2. Tag Filter
    if (store.selectedTag) {
        results = results.filter(p => p.tags?.includes(store.selectedTag))
    }

    return results
})

// [v11.0] Tag Aggregation
const allTags = computed(() => {
    const tags = new Set<string>()
    store.projects.forEach(p => p.tags?.forEach(t => tags.add(t)))
    return Array.from(tags).sort()
})

// Categories
const draftProjects = computed(() => filteredProjects.value.filter(p => p.stats.percentage === 0))
const activeProjects = computed(() => filteredProjects.value.filter(p => p.stats.percentage > 0 && p.stats.percentage < 100))
const completedProjects = computed(() => filteredProjects.value.filter(p => p.stats.percentage === 100))

async function handleAction(action: string, path: string) {
    try {
        await store.executeAction(action, path)
    } catch (e: any) {
        console.error(e)
    }
}

// [v11.1] Total Resource Consumption
const totalMonitorStats = computed(() => {
    let cpu = 0
    let ram = 0
    const active = store.projects.filter(p => p.process?.is_running)
    active.forEach(p => {
        if (p.process?.stats) {
            cpu += p.process.stats.cpu
            ram += p.process.stats.ram
        }
    })
    return { 
        cpu: cpu.toFixed(1), 
        ram: ram.toFixed(1),
        count: active.length
    }
})
</script>

<template>
  <div class="space-y-16">
      <!-- [v11.0] Tag Bar -->
      <div v-if="allTags.length > 0" class="flex flex-wrap items-center gap-3 animate-fade-in-up">
          <button 
            @click="store.selectedTag = ''"
            :class="!store.selectedTag ? 'bg-accent/20 text-accent border-accent/20 shadow-[0_0_15px_rgba(139,92,246,0.2)]' : 'bg-surface/30 border-white/5 text-secondary hover:text-primary'"
            class="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all"
          >
            All Sources
          </button>
          <button 
            v-for="tag in allTags" 
            :key="tag"
            @click="store.selectedTag = tag"
            :class="store.selectedTag === tag ? 'bg-accent/20 text-accent border-accent/20 shadow-[0_0_15px_rgba(139,92,246,0.2)]' : 'bg-surface/30 border-white/5 text-secondary hover:text-primary'"
            class="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all flex items-center"
          >
            <span class="opacity-40 mr-1.5 text-[8px]">#</span>{{ tag }}
          </button>
      </div>

      <!-- Empty State -->
      <div v-if="store.projects.length === 0 && store.isConnected" class="text-center py-20">
         <p class="text-lg mb-2 font-display text-primary">No projects monitored yet.</p>
         <p class="text-sm text-secondary">Click "Add Source" to scan and import your task projects.</p>
      </div>
      
      <!-- No Results State -->
      <div v-else-if="filteredProjects.length === 0 && store.searchQuery" class="text-center py-20 animate-fade-in">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-void border border-border mb-6">
              <svg class="w-8 h-8 text-secondary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
          </div>
          <p class="text-lg mb-2 font-display text-primary">No matching projects found</p>
          <p class="text-sm text-secondary">Try a different search term or clear the filter.</p>
          <button @click="store.searchQuery = ''" class="mt-6 text-xs text-accent font-bold hover:underline">Clear Search</button>
      </div>

      <div v-else class="space-y-16 animate-fade-in-up">
          <!-- Multi-process Dashboard (Always visible if running) -->
          <ProcessDashboard v-if="layoutMode === 'list'" />
          
          <!-- LAYOUT: Categorized List (Default) -->
          <div v-if="layoutMode === 'list'" class="space-y-16">
              <!-- Section 1: In Progress -->
              <section>
                  <div class="flex items-center space-x-4 mb-6">
                      <h2 class="text-xl font-display font-bold text-primary">In Progress</h2>
                      <div class="h-[1px] flex-1 bg-accent/30"></div>
                      <span class="text-xs font-mono text-accent px-2 py-1 bg-accent/5 border border-accent/20 rounded font-bold">{{ activeProjects.length }}</span>
                  </div>
                  
                  <div v-if="activeProjects.length === 0" class="py-12 border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-secondary">
                      <p class="font-mono text-sm opacity-75">No active projects. Start something!</p>
                  </div>
                  <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <ProjectCard v-for="p in activeProjects" :key="p.path" :project="p" />
                  </div>
              </section>

              <!-- Section 2: Drafts (Not Started) -->
              <section v-if="draftProjects.length > 0">
                  <div class="flex items-center space-x-4 mb-6">
                      <h2 class="text-xl font-display font-medium text-secondary">Drafts</h2>
                      <div class="h-[1px] flex-1 bg-border/50"></div>
                      <span class="text-xs font-mono text-secondary px-2 py-1 bg-surface border border-border rounded">{{ draftProjects.length }}</span>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <ProjectCard v-for="p in draftProjects" :key="p.path" :project="p" />
                  </div>
              </section>
              
              <!-- Section 3: Completed -->
              <section v-if="completedProjects.length > 0" class="opacity-80 hover:opacity-100 transition-opacity">
                   <div class="flex items-center space-x-4 mb-6">
                      <h2 class="text-xl font-display font-medium text-success">Completed</h2>
                      <div class="h-[1px] flex-1 bg-success/30"></div>
                      <span class="text-xs font-mono text-success px-2 py-1 bg-success/5 border border-success/20 rounded">{{ completedProjects.length }}</span>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <ProjectCard v-for="p in completedProjects" :key="p.path" :project="p" />
                  </div>
              </section>
          </div>

          <!-- LAYOUT: Pure Responsive Grid -->
          <div v-else-if="layoutMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              <ProjectCard v-for="p in filteredProjects" :key="p.path" :project="p" />
          </div>

          <!-- LAYOUT: Monitor Matrix (v11.1 - Horizontal Row Mode) -->
          <div v-else-if="layoutMode === 'monitor'" class="space-y-8 min-h-[60vh]">
               <!-- [v11.1] Global Infrastructure Status Bar -->
               <div v-if="totalMonitorStats.count > 0" class="flex items-center justify-between px-10 py-8 bg-white/[0.02] border border-white/5 rounded-[2.5rem] mb-12 shadow-2xl backdrop-blur-3xl ring-1 ring-white/5 animate-fade-in-up">
                   <div class="flex items-center space-x-12">
                       <div class="flex flex-col">
                           <span class="text-[9px] font-black uppercase tracking-[0.4em] text-accent mb-2">Command Center</span>
                           <h4 class="text-xs font-mono font-black text-primary/80">GLOBAL RESOURCE POOL</h4>
                       </div>
                       <div class="h-12 w-[1px] bg-white/10 hidden sm:block"></div>
                       <div class="flex items-center space-x-16">
                           <div class="flex flex-col">
                               <span class="text-[8px] text-secondary/40 uppercase font-black mb-1.5 tracking-widest">Total CPU</span>
                               <span class="text-4xl font-mono font-black text-primary tracking-tighter">{{ totalMonitorStats.cpu }}<span class="text-sm ml-1 opacity-30">%</span></span>
                           </div>
                           <div class="flex flex-col">
                               <span class="text-[8px] text-secondary/40 uppercase font-black mb-1.5 tracking-widest">Global Memory</span>
                               <span class="text-4xl font-mono font-black text-primary tracking-tighter">{{ totalMonitorStats.ram }}<span class="text-sm ml-1 opacity-30">MB</span></span>
                           </div>
                       </div>
                   </div>
                   <div class="hidden lg:flex flex-col items-end">
                       <div class="flex items-center space-x-3 text-[9px] font-black uppercase tracking-[0.2em] text-accent mb-2">
                           <span class="relative flex h-2 w-2">
                               <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                               <span class="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
                           </span>
                           <span>Telemetric Status: Active</span>
                       </div>
                       <span class="text-[8px] text-secondary/60 font-mono font-bold tracking-widest">{{ totalMonitorStats.count }} INSTANCES UNDER SURVEILLANCE</span>
                   </div>
               </div>

               <div v-if="totalMonitorStats.count === 0" class="text-center py-32 border border-dashed border-border rounded-3xl bg-white/[0.01]">
                   <svg class="w-12 h-12 text-secondary/60 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                       <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                   </svg>
                   <p class="text-secondary font-mono text-sm tracking-widest uppercase">No Active Streams Found</p>
                   <p class="text-[10px] text-secondary/50 mt-2">Activate project "Dev" mode to begin monitoring.</p>
               </div>
               <div v-else class="space-y-12">
                   <MonitorTile 
                        v-for="p in (store.projects.filter((p: any) => p.process?.is_running) as any[])" 
                        :key="p.path"
                        :project="p"
                        :logs="getLatestLogs(p.path)"
                        @action="handleAction"
                   />
               </div>
          </div>

      </div>
  </div>
</template>
