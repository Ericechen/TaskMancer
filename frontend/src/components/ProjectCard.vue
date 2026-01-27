<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Project } from '../stores/projectStore'
import LogConsole from './LogConsole.vue'
import ProjectGitInfo from './ProjectGitInfo.vue'
import ProjectRuntime from './ProjectRuntime.vue'

import { useProjectActions } from '../composables/useProjectActions'

const props = defineProps<{
  project: Project
}>()

const showConsole = ref(false)

const { 
    isUnlinking, 
    isDeleting, 
    handleUnlink, 
    handleDelete, 
    handleAction, 
    toggleDev, 
    handleFileChange, 
    handleInfo 
} = useProjectActions()

// [v13.28] Refactor: Dev Switch UI Logic (Code Review Feedback)
const switchButtonClass = computed(() => {
    const proc = props.project.process
    if (!proc) return 'bg-white/10 cursor-pointer'
    
    if (proc.alert_level === 'starting') return 'bg-warning/50 animate-pulse cursor-not-allowed'
    if (proc.alert_level === 'stopping') return 'bg-danger/50 animate-pulse cursor-not-allowed'
    if (proc.is_running) return 'bg-success/50 cursor-pointer'
    
    return 'bg-white/10 cursor-pointer'
})

const switchKnobClass = computed(() => {
    const proc = props.project.process
    // Default to 'off' (left) if no process
    if (!proc) return 'translate-x-0'
    
    // Force 'Off' (left) position when stopping
    if (proc.alert_level === 'stopping') return 'translate-x-0'
    
    // 'On' (right) position when starting OR running
    if (proc.alert_level === 'starting' || proc.is_running) return 'translate-x-3.5'
    
    return 'translate-x-0'
})

function formatSize(bytes?: number): string {
    if (bytes === undefined) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let val = bytes
    let unitIndex = 0
    while (val >= 1024 && unitIndex < units.length - 1) {
        val /= 1024
        unitIndex++
    }
    return `${val.toFixed(1)} ${units[unitIndex]}`
}
</script>

<template>
  <div class="bg-transparent border border-border p-5 flex flex-col h-full hover:border-accent/50 transition-all duration-300 relative group rounded-xl">
    <!-- Action Buttons (visible on hover) -->
    <div class="absolute top-4 right-4 flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-all z-10">
        <!-- Unlink Button -->
        <button 
            @click="handleUnlink(project)"
            :disabled="isUnlinking || isDeleting"
            class="p-1.5 text-border hover:text-accent transition-colors disabled:opacity-50"
            title="Remove Track (Keep Files)"
        >
            <svg v-if="isUnlinking" class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 105.656 5.656l1.1 1.1" />
                <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" />
            </svg>
        </button>

        <!-- Delete Folder Button -->
        <button 
            @click="handleDelete(project)"
            :disabled="isDeleting || isUnlinking"
            class="p-1.5 text-border hover:text-danger transition-colors disabled:opacity-50"
            title="Delete Folder from Disk"
        >
            <svg v-if="isDeleting" class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
        </button>
    </div>

    <!-- Header -->
    <div class="mb-4">
      <div class="flex flex-col mb-1 gap-1.5 pr-16">
          <div class="flex items-center space-x-2">
              <div :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', project.stats.percentage === 100 ? 'bg-success' : 'bg-accent']"></div>
              <h3 class="text-lg font-display font-medium text-primary tracking-tight truncate">{{ project.name }}</h3>
              
              <!-- Process Badge (v10.4) -->
              <div 
                v-if="project.process?.is_running" 
                :class="[
                    'flex items-center space-x-2 px-2 py-0.5 rounded-full ml-1 border',
                    (project.process.alert_level === 'critical' || project.process.has_error) ? 'bg-danger/20 border-danger text-danger' : 
                    project.process.alert_level === 'warning' ? 'bg-warning/20 border-warning text-warning' : 
                    'bg-accent/10 border-accent/20 text-accent'
                ]"
              >
                  <span :class="['w-1.5 h-1.5 rounded-full animate-pulse', project.process.has_error ? 'bg-danger' : 'bg-success']"></span>
                  <span class="text-[9px] font-bold uppercase tracking-tighter">LIVE</span>
              </div>
          </div>
          <p class="text-[10px] text-secondary font-mono truncate opacity-80 pl-3.5" :title="project.path">
              {{ project.path }}
          </p>
      </div>
          
          <!-- Meta Info Container -->
          <div class="flex flex-col gap-1 pl-3.5 mt-1 relative">
              <ProjectGitInfo :project="project" />
              <ProjectRuntime :project="project" />
          </div>
      </div>

    <!-- Quick Actions -->
    <div class="flex items-start justify-between mb-4 pl-3.5 pr-2 gap-4">
        <div class="flex flex-wrap items-center gap-2 min-w-0">
            <button 
              @click="handleAction('antigravity .', project.path)"
              class="flex items-center px-3 py-1.5 rounded-lg bg-accent/10 border border-accent/20 text-accent text-[10px] font-bold hover:bg-accent hover:text-white transition-all shadow-sm shrink-0"
            >
              Antigravity
            </button>

            <!-- Dev Switch (v10.5) -->
            <div v-if="project.hasStartBat" class="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg bg-surface/50 border border-white/5 shadow-sm shrink-0">
                <span class="text-[9px] font-black uppercase tracking-widest text-secondary/60">Dev</span>
                <!-- [v13.19] 啟動中狀態禁用 switch -->
                <!-- [v13.27] 停止中狀態禁用 switch 並顯示特效 -->
                <button 
                    @click="toggleDev(project)"
                    :disabled="project.process?.alert_level === 'starting' || project.process?.alert_level === 'stopping'"
                    class="relative inline-flex h-3.5 w-7 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
                    :class="switchButtonClass"
                >
                    <span 
                        class="pointer-events-none inline-block h-2.5 w-2.5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                        :class="switchKnobClass"
                    />
                </button>
                <span v-if="project.process?.alert_level === 'starting'" class="text-[8px] text-warning animate-pulse font-bold">Starting...</span>
                <span v-else-if="project.process?.alert_level === 'stopping'" class="text-[8px] text-danger animate-pulse font-bold">Stopping...</span>
            </div>

            <button 
              v-if="project.hasReadme"
              @click="handleInfo(project)"
              class="flex items-center px-3 py-1.5 rounded-lg bg-surface/50 border border-white/5 text-secondary text-[10px] font-bold hover:bg-white/5 hover:text-primary transition-all shadow-sm shrink-0"
            >
              Info
            </button>
            
            <button 
              @click="showConsole = true"
              class="flex items-center px-3 py-1.5 rounded-lg bg-surface/50 border border-white/5 text-secondary text-[10px] font-bold hover:bg-white/5 hover:text-accent transition-all shadow-sm shrink-0"
              title="View Live Logs"
            >
              <svg class="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 00-2 2z" />
              </svg>
              Logs
            </button>
        </div>

        <!-- Upload Button (Sticky Top-Right) -->
        <div class="relative shrink-0">
            <input 
              type="file" 
              class="hidden" 
              :id="'file-upload-' + project.name"
              @change="handleFileChange($event, project.path)"
              multiple
            >
            <label 
              :for="'file-upload-' + project.name"
              class="flex items-center justify-center p-1.5 cursor-pointer text-secondary/60 hover:text-accent transition-colors bg-white/5 rounded-lg border border-transparent hover:border-accent/20"
              title="Upload Task Spec"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </label>
        </div>
    </div>

    <!-- Stats Grid -->
    <div class="flex items-baseline space-x-8 text-sm mb-5 pl-3.5 mt-4">
       <div class="flex flex-col">
           <span class="text-[9px] text-secondary/90 uppercase tracking-[0.1em] font-bold mb-0.5">Progress</span>
           <span class="font-mono font-bold text-lg leading-tight" :class="project.stats.percentage === 100 ? 'text-success' : 'text-primary'">{{ project.stats.percentage }}%</span>
       </div>
       <div class="flex flex-col">
           <span class="text-[9px] text-secondary/90 uppercase tracking-[0.1em] font-bold mb-0.5">Done Tasks</span>
           <span class="font-mono text-secondary text-lg leading-tight">{{ project.stats.completed }}<span class="mx-1 opacity-30">/</span>{{ project.stats.total }}</span>
       </div>
    </div>

    <!-- Progress Line -->
    <div class="w-full bg-white/5 h-[1.5px] mb-4 overflow-hidden relative">
      <div 
        class="h-full absolute top-0 left-0 transition-all duration-700 ease-in-out"
        :class="project.stats.percentage === 100 ? 'bg-success shadow-[0_0_8px_rgba(34,197,94,0.4)]' : 'bg-accent shadow-[0_0_8px_rgba(139,92,246,0.4)]'"
        :style="{ width: `${project.stats.percentage}%` }"
      ></div>
    </div>

    <!-- Footer: Environment & Metrics -->
    <div class="mt-0 flex items-center justify-between pl-3.5 pr-2 pt-3.5 pb-4 border-t border-white/5 opacity-80">
        <!-- Health Badges -->
        <div v-if="project.health" class="flex items-center space-x-1.5">
            <div 
                :class="project.health.has_node_modules ? 'bg-success/10 text-success border-success/20' : 'bg-white/5 text-secondary/70 border-white/5'" 
                class="px-1.5 py-0.5 rounded-md border text-[8px] font-bold tracking-tighter"
                title="node_modules"
            >NM</div>
            <div 
                :class="project.health.has_venv ? 'bg-success/10 text-success border-success/20' : 'bg-white/5 text-secondary/70 border-white/5'" 
                class="px-1.5 py-0.5 rounded-md border text-[8px] font-bold tracking-tighter"
                title="Python venv"
            >PY</div>
            
            <!-- Dep Audit Status (v7.1) -->
            <div 
                v-if="project.live?.dependency_audit?.status === 'ok'"
                class="px-1.5 py-0.5 rounded-md border border-success/20 bg-success/5 text-[8px] text-success/60 font-mono"
                :title="`Prod: ${project.live.dependency_audit.dep_count} | Dev: ${project.live.dependency_audit.dev_dep_count}`"
            >
                DEP:{{ project.live.dependency_audit.dep_count }}<span v-if="project.live.dependency_audit.dev_dep_count" class="opacity-40 ml-0.5">+{{ project.live.dependency_audit.dev_dep_count }}</span>
            </div>
        </div>
        
        <!-- Technical Metrics -->
        <div v-if="project.metrics" class="flex items-center space-x-2.5 text-[9px] font-mono text-secondary/80 italic">
            <!-- <span>{{ formatNumber(project.metrics.loc) }} loc</span> -->
            <span>{{ formatSize(project.metrics.size) }}</span>
            <span>{{ project.metrics.fileCount }} files</span>
        </div>
    </div>

    <!-- Task Tree Area -->
    <div class="mt-auto pt-4 pl-3.5">
        <button 
          @click="project.isExpanded = !project.isExpanded"
          class="flex items-center space-x-2 text-[10px] font-bold tracking-widest uppercase text-secondary/80 hover:text-accent transition-colors group/btn"
        >
          <span class="w-4 h-px bg-white/10 group-hover/btn:bg-accent transition-colors"></span>
          <span>{{ project.isExpanded ? 'Collapse' : 'Inspect tasks' }}</span>
          <svg 
            class="w-3 h-3 transition-transform duration-300"
            :class="project.isExpanded ? 'rotate-180' : ''"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Dynamic Task Tree -->
        <Transition
          enter-active-class="transition duration-300 ease-out"
          enter-from-class="opacity-0 -translate-y-2 scale-[0.98]"
          enter-to-class="opacity-100 translate-y-0 scale-100"
          leave-active-class="transition duration-200 ease-in"
          leave-from-class="opacity-100 translate-y-0 scale-100"
          leave-to-class="opacity-0 -translate-y-2 scale-[0.98]"
        >
          <div v-if="project.isExpanded" class="mt-5 space-y-4 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar">
            <div v-for="category in project.tasks" :key="category.text" class="space-y-2.5">
              <h4 class="text-[10px] font-bold text-accent/60 uppercase tracking-[0.2em] flex items-center">
                <span class="w-1 h-3 bg-accent/30 mr-2 rounded-full"></span>
                {{ category.text }}
              </h4>
              <ul class="space-y-2 pl-3 border-l border-white/5">
                <li v-for="task in category.children" :key="task.text" class="flex flex-col space-y-1">
                  <div class="flex items-start space-x-2 group/item">
                    <span :class="['mt-1.5 w-1 h-1 rounded-full flex-shrink-0 transition-colors', task.status === 'done' ? 'bg-success shadow-[0_0_5px_rgba(34,197,94,0.5)]' : 'bg-secondary/20']"></span>
                    <span :class="['text-xs leading-relaxed transition-colors', task.status === 'done' ? 'text-secondary/80 line-through' : 'text-primary/90 group-hover/item:text-primary']">
                      {{ task.text }}
                    </span>
                  </div>
                  <!-- Nested Child Tasks -->
                  <ul v-if="task.children?.length" class="pl-4 space-y-1.5 mt-1 border-l border-white/5 ml-0.5">
                    <li v-for="child in task.children" :key="child.text" class="flex items-start space-x-2 opacity-90">
                      <span :class="['mt-1.5 w-1 h-1 rounded-full scale-75', child.status === 'done' ? 'bg-success/50' : 'bg-secondary/10']"></span>
                      <span :class="['text-[11px]', child.status === 'done' ? 'text-secondary/70 line-through' : 'text-secondary/70']">
                        {{ child.text }}
                      </span>
                    </li>
                  </ul>
                </li>
              </ul>
            </div>
          </div>
        </Transition>
    </div>

    <!-- Log Console Modal (v10.3) -->
    <Teleport to="body">
        <LogConsole 
            :isOpen="showConsole" 
            :projectPath="project.path" 
            :projectName="project.name"
            @close="showConsole = false"
        />
    </Teleport>
  </div>
</template>

<style scoped>
.font-display { font-family: 'Plus Jakarta Sans', sans-serif; }
.font-mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }

.custom-scrollbar::-webkit-scrollbar {
  width: 3px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* README content styling */
:deep(.readme-content) {
    font-size: 14px;
    line-height: 1.6;
}
:deep(.readme-content h1) { font-size: 1.5rem; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem; color: #fff; }
:deep(.readme-content h2) { font-size: 1.25rem; margin-top: 1.5rem; margin-bottom: 0.75rem; color: #8b5cf6; }
:deep(.readme-content p) { margin-bottom: 1rem; color: #9ca3af; }
:deep(.readme-content ul) { margin-bottom: 1rem; padding-left: 1.5rem; list-style-type: disc; }
:deep(.readme-content code) { background: rgba(255,255,255,0.1); padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }
:deep(.readme-content pre) { background: #1a1a1a; padding: 1rem; border-radius: 8px; overflow-x: auto; margin-bottom: 1rem; }
</style>
