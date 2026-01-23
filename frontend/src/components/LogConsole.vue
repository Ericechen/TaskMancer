<script setup lang="ts">
import { ref, onUpdated } from 'vue'
import { useProjectStore } from '../stores/projectStore'

const props = defineProps<{
    projectPath: string;
    projectName: string;
    isOpen: boolean;
}>()

const emit = defineEmits(['close'])
const store = useProjectStore()
const scrollContainer = ref<HTMLElement | null>(null)

function close() {
    emit('close')
}

async function stopProcess() {
    try {
        await store.executeAction('stop', props.projectPath)
    } catch (e) {
        console.error('Stop failed', e)
    }
}

// Auto scroll to bottom
onUpdated(() => {
    if (scrollContainer.value) {
        scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
})
</script>

<template>
    <Transition name="slide-up">
        <div v-if="isOpen" class="fixed inset-0 z-[60] flex items-center justify-center p-4 md:p-12">
            <!-- Fixed Backdrop -->
            <div @click="close" class="absolute inset-0 bg-void/60 backdrop-blur-sm"></div>

            <!-- Stable Modal Box (Glassmorphism matched with Info Panel) -->
            <div class="bg-[#080808]/90 backdrop-blur-3xl border border-white/10 w-full max-w-5xl h-full max-h-[85vh] rounded-3xl overflow-hidden shadow-2xl flex flex-col relative ring-1 ring-white/10 animate-fade-in-up">
                <!-- Header -->
                <div class="flex items-center justify-between px-8 py-6 border-b border-white/10 bg-white/[0.02]">
                    <div class="flex items-center space-x-4 text-primary">
                        <div class="w-10 h-10 rounded-xl bg-accent shadow-lg shadow-accent/40 flex items-center justify-center text-white">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 00-2 2z" />
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-xl font-display font-bold text-primary">{{ projectName }}</h3>
                            <p class="text-[10px] text-secondary font-mono uppercase tracking-[0.2em] mt-0.5">Managed Service Logs</p>
                        </div>
                    </div>
                    
                    <div class="flex items-center space-x-3">
                        <button 
                            @click="stopProcess"
                            class="px-5 py-2 rounded-xl bg-danger/10 border border-danger/20 text-danger text-xs font-bold hover:bg-danger hover:text-white transition-all flex items-center space-x-2"
                        >
                            <span class="w-2 h-2 rounded-full bg-danger animate-pulse"></span>
                            <span>Stop Process</span>
                        </button>
                        <button 
                            @click="close"
                            class="p-2 text-secondary hover:text-primary transition-colors bg-white/5 rounded-full"
                        >
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Console Output -->
                <div 
                    ref="scrollContainer"
                    class="flex-1 overflow-y-auto p-8 font-mono text-[13px] leading-relaxed custom-scrollbar bg-white/[0.01]"
                >
                    <div v-if="!store.projectLogs[projectPath] || store.projectLogs[projectPath].length === 0" class="h-full flex flex-col items-center justify-center text-zinc-600">
                        <svg class="w-12 h-12 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <p class="animate-pulse italic opacity-40">Connecting to stream...</p>
                    </div>
                    <div v-else class="space-y-1">
                        <div v-for="(line, idx) in store.projectLogs[projectPath]" :key="idx" class="group flex">
                            <span class="text-zinc-600 mr-4 select-none w-8 text-right font-bold">{{ idx + 1 }}</span>
                            <span class="text-zinc-200 break-all whitespace-pre-wrap">{{ line }}</span>
                        </div>
                    </div>
                </div>

                <!-- Footer Stats -->
                <div class="px-8 py-3 bg-white/[0.03] border-t border-white/10 flex items-center justify-between text-[10px] font-mono text-secondary">
                    <div class="flex items-center space-x-5">
                        <span class="flex items-center text-success"><span class="w-2 h-2 rounded-full bg-success mr-2"></span>STDOUT LIVE</span>
                        <span class="opacity-50 tracking-widest">BUFFER: {{ store.projectLogs[projectPath]?.length || 0 }}/500 lines</span>
                    </div>
                    <div class="uppercase tracking-[0.2em] opacity-30">Stream Protocol v2 (WebSocket)</div>
                </div>
            </div>
        </div>
    </Transition>
</template>

<style scoped>
.font-display { font-family: 'Plus Jakarta Sans', sans-serif; }
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }

.slide-up-enter-active, .slide-up-leave-active {
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from { opacity: 0; transform: translateY(20px); }
.slide-up-leave-to { opacity: 0; transform: translateY(20px); }
</style>
