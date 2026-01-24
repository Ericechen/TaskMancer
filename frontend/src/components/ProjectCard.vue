<script setup lang="ts">
import { ref } from 'vue'
import type { Project } from '../stores/projectStore'
import { useProjectStore } from '../stores/projectStore'
import Swal from 'sweetalert2'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import LogConsole from './LogConsole.vue'

const props = defineProps<{
  project: Project
}>()

const projectStore = useProjectStore()
const isUnlinking = ref(false)
const isDeleting = ref(false)
const showConsole = ref(false)

async function handleUnlink(path: string) {
    const result = await Swal.fire({
        title: 'Remove Project?',
        html: `Are you sure you want to stop tracking <b>${props.project.name}</b>?<br><small class="opacity-50">This will only remove it from the dashboard.</small>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, remove',
        cancelButtonText: 'Cancel'
    })

    if (result.isConfirmed) {
        isUnlinking.value = true
        try {
            await projectStore.removeProject(path, false)
            Swal.fire({
                title: 'Removed!',
                text: 'Project tracking removed.',
                icon: 'success',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            })
        } catch (e: any) {
            Swal.fire('Error', e.message, 'error')
        } finally {
            isUnlinking.value = false
        }
    }
}

async function handleDelete(path: string) {
    const result = await Swal.fire({
        title: 'DELETE FOLDER?',
        html: `THIS IS IRREVERSIBLE!<br>Do you really want to delete <b>${props.project.name}</b> and all its files from disk?`,
        icon: 'error',
        showCancelButton: true,
        customClass: {
            confirmButton: 'bg-danger hover:bg-danger/80'
        },
        confirmButtonText: 'DELETE EVERYTHING',
        cancelButtonText: 'Cancel'
    })

    if (result.isConfirmed) {
        isDeleting.value = true
        try {
            await projectStore.removeProject(path, true)
            Swal.fire({
                title: 'Deleted!',
                text: 'Project folder has been deleted.',
                icon: 'success',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            })
        } catch (e: any) {
            Swal.fire('Error', e.message, 'error')
        } finally {
            isDeleting.value = false
        }
    }
}

async function handleAction(action: string, path: string) {
  try {
    await projectStore.executeAction(action, path)
  } catch (e: any) {
    Swal.fire('Action Failed', e.message, 'error')
  }
}

async function toggleDev() {
    const isRunning = props.project.process?.is_running;
    if (isRunning) {
        // Handle stopping with confirmation
        const result = await Swal.fire({
            title: 'Stop Service?',
            html: `Are you sure you want to terminate <b class="text-accent">${props.project.name}</b>?`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, Stop',
            cancelButtonText: 'Cancel'
        })
        if (result.isConfirmed) {
            handleAction('stop', props.project.path)
        }
    } else {
        // Start silently (v10.5)
        handleAction('start.bat', props.project.path)
    }
}

async function handleFileChange(event: Event, path: string) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    try {
      await projectStore.uploadFiles(path, target.files)
      Swal.fire({
          title: 'Uploaded!',
          text: 'Files uploaded successfully.',
          icon: 'success',
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: 3000
      })
    } catch (e: any) {
      Swal.fire('Upload Failed', e.message, 'error')
    }
  }
}

async function handleInfo(path: string) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/projects/readme?path=${encodeURIComponent(path)}`)
        if (!response.ok) throw new Error('Failed to fetch README')
        const data = await response.json()
        
        const htmlContent = DOMPurify.sanitize(await marked(data.content))
        
        Swal.fire({
            html: `
                <div class="text-left">
                    <div class="flex items-center space-x-3 mb-8 border-b border-white/5 pb-6">
                        <div class="w-10 h-10 rounded-xl bg-accent/20 flex items-center justify-center text-accent">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                        </div>
                        <div>
                            <h2 class="text-xl font-display font-bold text-primary m-0">${props.project.name}</h2>
                            <p class="text-xs text-secondary/50 font-mono m-0 uppercase tracking-widest mt-0.5">Project Documentation</p>
                        </div>
                    </div>
                    <div class="tm-readme-content">${htmlContent}</div>
                </div>
            `,
            width: '850px',
            background: 'rgba(5, 5, 5, 0.95)',
            color: '#F8FAFC',
            backdrop: 'rgba(0,0,0,0.8)',
            showCloseButton: true,
            showConfirmButton: false,
            customClass: {
                popup: 'rounded-3xl border border-white/10 shadow-2xl backdrop-blur-xl p-8',
                htmlContainer: 'p-0 m-0 overflow-hidden'
            },
            showClass: {
                popup: 'animate__animated animate__fadeInUp animate__faster'
            },
            hideClass: {
                popup: 'animate__animated animate__fadeOutDown animate__faster'
            }
        })
    } catch (e: any) {
        Swal.fire({
            icon: 'error',
            title: 'Failed to load README',
            text: e.message || 'Error occurred while fetching documentation',
            background: '#0a0a0a',
            color: '#e5e7eb',
            customClass: {
                popup: 'rounded-2xl border border-white/10'
            }
        })
    }
}


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
  <div class="bg-transparent border border-border p-5 flex flex-col h-full hover:border-accent/50 transition-colors duration-300 relative group rounded-xl">
    <!-- Action Buttons (visible on hover) -->
    <div class="absolute top-4 right-4 flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-all z-10">
        <!-- Unlink Button -->
        <button 
            @click="handleUnlink(project.path)"
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
            @click="handleDelete(project.path)"
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
              <div v-if="project.process?.is_running" class="flex items-center space-x-2 bg-accent/10 border border-accent/20 px-2 py-0.5 rounded-full ml-1">
                  <span :class="['w-1.5 h-1.5 rounded-full animate-pulse', project.process.has_error ? 'bg-danger' : 'bg-success']"></span>
                  <span class="text-[9px] font-bold text-accent uppercase tracking-tighter">Running</span>
              </div>
          </div>
          <p class="text-[10px] text-secondary font-mono truncate opacity-80 pl-3.5" :title="project.path">
              {{ project.path }}
          </p>
      </div>
          
      <!-- Status Rows Container -->
      <div class="flex flex-col gap-1.5 pl-3.5 mt-1 relative">
          
          <!-- Row 1: Git Info -->
          <div v-if="project.git && project.git.is_git" class="flex items-center w-full gap-x-3 gap-y-1 text-[10px] font-mono flex-wrap">
                  <!-- Branch -->
                  <div class="flex items-center text-primary/80">
                      <svg class="w-3 h-3 mr-1 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                      </svg>
                      <span>{{ project.git.branch }}</span>
                  </div>
                  
                  <!-- Sync Status -->
                  <div v-if="project.git.sync_status && project.git.sync_status !== 'Not checked'" class="flex items-center px-1.5 py-0.25 rounded bg-surface/50 border border-border/30">
                      <span :class="{
                          'text-success/90': project.git.sync_status === 'Synced',
                          'text-accent/90': project.git.sync_status.includes('Ahead'),
                          'text-warning/90': project.git.sync_status.includes('Behind') || project.git.sync_status.includes('Diverged')
                      }">{{ project.git.sync_status }}</span>
                  </div>

                  <!-- Uncommitted -->
                  <div v-if="project.git.uncommitted > 0" class="text-danger flex items-center">
                      <span class="w-1 h-1 rounded-full bg-danger animate-pulse mr-1"></span>
                      {{ project.git.uncommitted }} changes
                  </div>

                  <!-- Momentum (Right Aligned in Row 1) -->
                  <div v-if="project.momentum !== undefined" class="ml-auto flex items-center text-secondary/80" title="Activities (Commits) in last 7 days">
                      <svg class="w-3 h-3 mr-1 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span>{{ project.momentum }} act</span>
                  </div>
              </div>

              <!-- Row 2: Live Ports -->
              <div v-if="project.hasConfig && project.live?.active_ports?.length" class="flex items-center flex-wrap gap-1 pr-12">
                  <a 
                      v-for="item in project.live.active_ports" 
                      :key="item.port"
                      :href="item.status === 'online' ? `http://localhost:${item.port}` : 'javascript:void(0)'"
                      target="_blank"
                      :class="[
                          'flex items-center space-x-1 px-1.5 py-0.25 rounded border text-[9px] font-bold transition-all',
                          item.status === 'online' 
                            ? 'bg-success/10 border-success/30 text-success' 
                            : 'bg-void/50 border-border/50 text-secondary opacity-50 cursor-not-allowed'
                      ]"
                      :title="item.status === 'online' ? `Open ${item.label || 'service'} on port ${item.port}` : `${item.label || 'Service'} is offline`"
                  >
                      <span :class="['w-1.5 h-1.5 rounded-full', item.status === 'online' ? 'bg-success animate-pulse' : 'bg-void border border-secondary/30']"></span>
                      <span>{{ item.label || 'Live' }}: {{ item.port }}</span>
                  </a>
              </div>
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
                <button 
                    @click="toggleDev"
                    class="relative inline-flex h-3.5 w-7 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                    :class="project.process?.is_running ? 'bg-success/50' : 'bg-white/10'"
                >
                    <span 
                        class="pointer-events-none inline-block h-2.5 w-2.5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                        :class="project.process?.is_running ? 'translate-x-3.5' : 'translate-x-0'"
                    />
                </button>
            </div>

            <button 
              v-if="project.hasReadme"
              @click="handleInfo(project.path)"
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
