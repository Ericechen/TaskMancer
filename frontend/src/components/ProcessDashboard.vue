<script setup lang="ts">
import { computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { $swal } from '../utils/swal'

const store = useProjectStore()

const runningProjects = computed(() => {
    return store.projects.filter(p => p.process?.is_running)
})

async function stopProcess(path: string, name: string) {
    const result = await $swal.fire({
        title: 'Stop Service?',
        html: `Are you sure you want to terminate <b class="text-accent">${name}</b>? <br/>This will kill all active child processes.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Stop Service',
        cancelButtonText: 'Go Back'
    })

    if (result.isConfirmed) {
        try {
            await store.executeAction('stop', path)
        } catch (e: any) {
            $swal.fire('Error', e.message, 'error')
        }
    }
}
</script>

<template>
    <div v-if="runningProjects.length > 0" class="mb-12">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-xs font-bold uppercase tracking-[0.3em] text-accent/60 flex items-center">
                <span class="w-8 h-px bg-accent/30 mr-4"></span>
                Active Processes ({{ runningProjects.length }})
            </h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div 
                v-for="project in runningProjects" 
                :key="project.path"
                class="bg-surface/30 backdrop-blur-md border border-white/5 rounded-2xl p-4 flex items-center justify-between group hover:border-accent/30 transition-all shadow-lg"
            >
                <div class="flex items-center space-x-4">
                    <div class="relative">
                        <div class="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <span v-if="project.process?.has_error" class="absolute -top-1 -right-1 w-4 h-4 bg-danger rounded-full flex items-center justify-center border-2 border-void animate-bounce">
                            <span class="text-[8px] text-white font-bold">!</span>
                        </span>
                    </div>
                    
                    <div>
                        <h3 class="text-sm font-bold text-primary truncate max-w-[150px]">{{ project.name }}</h3>
                        <div class="flex items-center space-x-3 mt-1 font-mono text-[10px]">
                            <span class="text-success">{{ project.process?.stats?.cpu }}% CPU</span>
                            <span class="text-secondary/60">{{ project.process?.stats?.ram }} MB</span>
                        </div>
                    </div>
                </div>

                <button 
                    @click="stopProcess(project.path, project.name)"
                    class="p-2 rounded-lg bg-danger/10 text-danger opacity-0 group-hover:opacity-100 transition-opacity hover:bg-danger hover:text-white"
                    title="Stop Process"
                >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    </div>
</template>
