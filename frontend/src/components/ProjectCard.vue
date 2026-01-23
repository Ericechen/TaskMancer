<script setup lang="ts">
import { ref } from 'vue'
import { useProjectStore, type Project } from '../stores/projectStore'
import TaskTree from './TaskTree.vue'
import { $swal, Toast } from '../utils/swal'
import { marked } from 'marked'

const props = defineProps<{
  project: Project
}>()

const store = useProjectStore()
const isOpen = ref(false)
const isDeleting = ref(false)
const isUnlinking = ref(false)

const isUploading = ref(false)
const isRunningCommand = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

async function handleCommand(cmd: 'open' | 'dev') {
    isRunningCommand.value = true
    try {
        await store.runCommand(props.project.path, cmd)
    } catch (e: any) {
        $swal.fire({
            icon: 'error',
            title: 'Command Failed',
            text: e.message || 'Error executing command'
        })
    } finally {
        isRunningCommand.value = false
    }
}

async function handleUnlink(path: string) {
    const result = await $swal.fire({
        title: 'Unlink Project?',
        html: `
            <div class="text-sm text-secondary mb-4 text-left">Stop monitoring this project? The local files will strictly remain on your disk.</div>
            <div class="bg-black/20 p-3 rounded border border-white/5 font-mono text-[10px] break-all text-left opacity-70">${path}</div>
        `,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, Unlink',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#8b5cf6',
    })

    if (!result.isConfirmed) return
    
    isUnlinking.value = true
    const success = await store.removeProject(path, false)
    isUnlinking.value = false
    
    if (success) {
        Toast.fire({
            icon: 'success',
            title: 'Project unlinked'
        })
    }
}

async function handleDelete(path: string) {
    const result = await $swal.fire({
        title: 'DELETE FOLDER?',
        html: `
            <div class="text-sm text-danger/80 mb-4 text-left font-bold">WARNING: This will PERMANENTLY delete the entire directory! This action cannot be undone.</div>
            <div class="bg-black/20 p-3 rounded border border-white/5 font-mono text-[10px] break-all text-left opacity-70 mb-2">${path}</div>
        `,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, Delete Everything',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#ef4444',
    })

    if (!result.isConfirmed) return
    
    isDeleting.value = true
    const success = await store.removeProject(path, true)
    isDeleting.value = false
    
    if (success) {
        Toast.fire({
            icon: 'success',
            title: 'Folder permanently deleted'
        })
    }
}

function triggerUpload() {
    fileInput.value?.click()
}

async function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement
        if (input.files && input.files.length > 0) {
            const file = input.files[0]
            if (!file) return // Satisfy TS
            isUploading.value = true
            try {
                await store.uploadProjectFile(props.project.path, file)
                Toast.fire({
                    icon: 'success',
                    title: 'File uploaded successfully'
                })
            } catch (e: any) {
            $swal.fire({
                icon: 'error',
                title: 'Upload Failed',
                text: e.message || 'Unknown error occurred'
            })
        } finally {
            isUploading.value = false
            input.value = '' // Reset
        }
    }
}

async function handleInfo() {
    try {
        const content = await store.fetchReadme(props.project.path)
        const html = await marked(content)
        
        $swal.fire({
            title: `
                <div class="flex flex-col items-center">
                    <span class="text-accent text-xl font-display font-bold">${props.project.name}</span>
                    <span class="text-[10px] text-secondary font-mono opacity-50 mt-1">${props.project.path}</span>
                </div>
            `,
            html: `
                <div class="tm-readme-content text-left max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
                    ${html}
                </div>
            `,
            width: '850px',
            background: '#121212',
            color: '#F8FAFC',
            confirmButtonText: 'Done Reading',
            confirmButtonColor: '#8B5CF6',
            customClass: {
                popup: 'rounded-2xl border border-white/5 shadow-2xl backdrop-blur-xl',
                confirmButton: 'px-8 py-2 rounded-lg font-bold tracking-tight'
            },
            showClass: {
                popup: 'animate-fade-in-up'
            }
        })
    } catch (e: any) {
        $swal.fire({
            icon: 'error',
            title: 'Failed to load README',
            text: e.message || 'Error occurred while fetching documentation'
        })
    }
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
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
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
    <div class="mb-4 pr-16">
      <div class="flex flex-col mb-1 gap-1.5">
          <div class="flex items-center space-x-2">
              <div :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', project.stats.percentage === 100 ? 'bg-success' : 'bg-accent']"></div>
              <h3 class="text-lg font-display font-medium text-primary tracking-tight truncate">{{ project.name }}</h3>
          </div>
          <p class="text-[10px] text-secondary font-mono truncate opacity-60 pl-3.5" :title="project.path">
              {{ project.path }}
          </p>
          <!-- GitHub Tags (Moved below path) -->
          <div v-if="project.links && project.links.length > 0" class="flex flex-wrap gap-1 pl-3.5 mt-1">
              <a 
                v-for="(link, idx) in project.links" 
                :key="idx"
                :href="link"
                target="_blank"
                class="text-[9px] bg-accent/10 text-accent px-2 py-0.5 rounded border border-accent/20 hover:bg-accent/20 transition-colors uppercase font-bold tracking-wider"
                :title="link"
                @click.stop
              >
                GitHub
              </a>
          </div>
      </div>
    </div>

    <!-- Quick Actions (Antigravity & Dev) -->
    <div class="flex items-center space-x-3 mb-6 pl-3.5">
        <button 
            @click="handleCommand('open')"
            :disabled="isRunningCommand"
            class="flex items-center space-x-2 text-[10px] font-bold text-primary/80 hover:text-primary transition-colors bg-white/5 px-3 py-1.5 rounded-lg border border-white/5 hover:border-white/10"
        >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71L12 2z" />
            </svg>
            <span>Antigravity</span>
        </button>
        <button 
            v-if="project.hasStartBat"
            @click="handleCommand('dev')"
            :disabled="isRunningCommand"
            class="flex items-center space-x-2 text-[10px] font-bold text-emerald-400 hover:text-emerald-300 transition-colors bg-emerald-500/5 px-3 py-1.5 rounded-lg border border-emerald-500/10 hover:border-emerald-500/30"
        >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Dev</span>
        </button>
        <button 
            v-if="project.hasReadme"
            @click="handleInfo"
            class="flex items-center space-x-2 text-[10px] font-bold text-sky-400 hover:text-sky-300 transition-colors bg-sky-500/5 px-3 py-1.5 rounded-lg border border-sky-500/10 hover:border-sky-500/30"
        >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Info</span>
        </button>
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


    <!-- Upload Spec Button (Only for Drafts/0%) -->
    <div v-if="project.stats.percentage === 0" class="mb-4 pl-3.5">
        <input 
            type="file" 
            ref="fileInput" 
            class="hidden" 
            @change="handleFileChange"
        >
        <button 
            @click="triggerUpload"
            :disabled="isUploading"
             class="group flex items-center space-x-2 text-xs font-bold text-accent hover:text-accent/80 transition-colors disabled:opacity-50"
        >
            <div class="w-6 h-6 rounded border border-accent/20 bg-accent/5 flex items-center justify-center group-hover:bg-accent/10 transition-colors">
                <svg v-if="isUploading" class="animate-spin w-3 h-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
            </div>
            <span>{{ isUploading ? 'Uploading...' : 'Upload Spec' }}</span>
        </button>
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
