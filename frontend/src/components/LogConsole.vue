<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import AnsiUp from 'ansi-to-html'

const props = defineProps<{
    projectPath: string;
    projectName: string;
    isOpen: boolean;
}>()

const emit = defineEmits(['close'])
const store = useProjectStore()
const scrollContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
const ansi = new AnsiUp({
    fg: '#F8FAFC',
    bg: 'transparent',
    newline: false,
    escapeXML: true,
})

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

function exportLogs() {
    const logs = store.projectLogs[props.projectPath] || []
    const blob = new Blob([logs.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `log-${props.projectName}-${new Date().toISOString().slice(0, 19).replace(/[:]/g, '-')}.log`
    a.click()
    URL.revokeObjectURL(url)
}

function parseAnsi(text: string) {
    return ansi.toHtml(text)
}

// Robust auto-scroll watcher
watch(
    () => store.projectLogs[props.projectPath]?.length,
    () => {
        if (autoScroll.value && scrollContainer.value) {
            nextTick(() => {
                if (scrollContainer.value) {
                    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
                }
            })
        }
    },
    { flush: 'post' }
)

// Initial scroll when opening
watch(() => props.isOpen, (open) => {
    if (open) {
        nextTick(() => {
            if (scrollContainer.value) {
                scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
            }
        })
    }
})

const project = computed(() => store.projects.find(p => p.path === props.projectPath))
const stats = computed(() => project.value?.process?.stats || null)
const history = computed(() => project.value?.process?.history || { cpu: [], ram: [] })
const currentLogs = computed(() => store.projectLogs[props.projectPath] || [])
const activeTab = ref<'logs' | 'performance'>('logs')

// [v11.0] Sparkline Generator
function generatePoints(data: number[], maxVal: number) {
    if (!data || data.length < 2) return ""
    const width = 800
    const height = 180
    const pointsCount = 300
    const step = width / (pointsCount - 1)
    
    // We only take the last 300 points
    return data.map((val, i) => {
        const x = i * step
        const y = height - (val / maxVal) * height
        return `${x},${y}`
    }).join(" ")
}

const cpuPoints = computed(() => generatePoints(history.value.cpu, 100))
const ramPoints = computed(() => {
    const maxVal = Math.max(...history.value.ram, 512)
    return generatePoints(history.value.ram, maxVal)
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
                            <div class="flex items-center space-x-3 mt-0.5">
                                <p class="text-[10px] text-secondary font-mono uppercase tracking-[0.2em]">Managed Service Logs</p>
                                <div v-if="stats" class="h-3 w-px bg-white/10"></div>
                                <div v-if="stats" class="flex items-center space-x-3 font-mono text-[9px] text-accent/80">
                                    <span>CPU: {{ stats.cpu }}%</span>
                                    <span>RAM: {{ stats.ram }}MB</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex items-center space-x-3">
                        <!-- [v11.0] Tab Switcher -->
                        <div class="flex bg-void/50 p-1 rounded-xl border border-white/5 mr-2">
                            <button 
                                @click="activeTab = 'logs'"
                                :class="activeTab === 'logs' ? 'bg-accent text-white shadow-lg shadow-accent/20' : 'text-secondary hover:text-primary'"
                                class="px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all"
                            >Logs</button>
                            <button 
                                @click="activeTab = 'performance'"
                                :class="activeTab === 'performance' ? 'bg-accent text-white shadow-lg shadow-accent/20' : 'text-secondary hover:text-primary'"
                                class="px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all"
                            >Performance</button>
                        </div>

                        <button 
                            @click="exportLogs"
                            class="p-2 text-secondary hover:text-primary transition-colors bg-white/5 rounded-lg flex items-center space-x-2 px-3"
                            title="Download Log Snapshot"
                        >
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-4l-4 4m0 0L8 8m4-4v12" />
                            </svg>
                            <span class="text-[10px] font-bold uppercase tracking-wider">Export</span>
                        </button>
                        
                        <div class="h-6 w-px bg-white/10 mx-1"></div>

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

                <!-- Content Area -->
                <div v-if="activeTab === 'logs'" class="flex-1 flex flex-col min-h-0">
                    <!-- Console Output -->
                    <div 
                        ref="scrollContainer"
                        class="flex-1 overflow-y-auto p-8 font-mono text-[13px] leading-relaxed custom-scrollbar bg-white/[0.01]"
                        style="overflow-anchor: none;"
                    >
                        <div v-if="currentLogs.length === 0" class="h-full flex flex-col items-center justify-center text-zinc-600">
                            <svg class="w-12 h-12 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <p class="animate-pulse italic opacity-40">Connecting to stream...</p>
                        </div>
                        <div v-else class="space-y-1">
                            <div v-for="(line, idx) in currentLogs" :key="idx" class="group flex">
                                <span class="text-zinc-600 mr-4 select-none w-8 text-right font-bold">{{ idx + 1 }}</span>
                                <span class="text-zinc-200 break-all whitespace-pre-wrap" v-html="parseAnsi(line)"></span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- [v11.0] Performance View -->
                <div v-else class="flex-1 p-12 bg-white/[0.01] overflow-y-auto custom-scrollbar">
                    <div class="grid grid-cols-1 gap-12 max-w-4xl mx-auto">
                        <!-- CPU Section -->
                        <section>
                            <div class="flex items-center justify-between mb-4">
                                <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-accent">CPU Usage Trend</h4>
                                <span class="text-2xl font-mono font-bold text-primary">{{ stats?.cpu }}%</span>
                            </div>
                            <div class="h-48 w-full bg-void rounded-2xl border border-white/5 relative overflow-hidden flex items-center justify-center">
                                <svg class="w-full h-full preserve-3d" viewBox="0 0 800 180" preserveAspectRatio="none">
                                    <defs>
                                        <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stop-color="#8B5CF6" stop-opacity="0.2" />
                                            <stop offset="100%" stop-color="#8B5CF6" stop-opacity="0" />
                                        </linearGradient>
                                    </defs>
                                    <path :d="`M ${cpuPoints} L 800 180 L 0 180 Z`" fill="url(#cpuGradient)" />
                                    <polyline 
                                        fill="none" 
                                        stroke="#8B5CF6" 
                                        stroke-width="2" 
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        :points="cpuPoints" 
                                        class="drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]"
                                    />
                                </svg>
                                <div v-if="!history.cpu.length" class="absolute inset-0 flex items-center justify-center text-xs text-secondary/60 italic font-mono">Initializing sensors...</div>
                            </div>
                        </section>

                        <!-- RAM Section -->
                        <section>
                            <div class="flex items-center justify-between mb-4">
                                <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-success">Memory usage Trend</h4>
                                <span class="text-2xl font-mono font-bold text-primary">{{ stats?.ram }} <span class="text-xs text-secondary">MB</span></span>
                            </div>
                            <div class="h-48 w-full bg-void rounded-2xl border border-white/5 relative overflow-hidden">
                                <svg class="w-full h-full" viewBox="0 0 800 180" preserveAspectRatio="none">
                                    <defs>
                                        <linearGradient id="ramGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stop-color="#10B981" stop-opacity="0.2" />
                                            <stop offset="100%" stop-color="#10B981" stop-opacity="0" />
                                        </linearGradient>
                                    </defs>
                                    <path :d="`M ${ramPoints} L 800 180 L 0 180 Z`" fill="url(#ramGradient)" />
                                    <polyline 
                                        fill="none" 
                                        stroke="#10B981" 
                                        stroke-width="2" 
                                        stroke-linecap="round" 
                                        stroke-linejoin="round"
                                        :points="ramPoints" 
                                        class="drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]"
                                    />
                                </svg>
                                <div v-if="!history.ram.length" class="absolute inset-0 flex items-center justify-center text-xs text-secondary/60 italic font-mono">Calibrating memory...</div>
                            </div>
                        </section>
                    </div>
                </div>

                <!-- Footer Stats -->
                <div class="px-8 py-3 bg-white/[0.03] border-t border-white/10 flex items-center justify-between text-[10px] font-mono text-secondary">
                    <div class="flex items-center space-x-6">
                        <span class="flex items-center text-success">
                            <span class="w-2 h-2 rounded-full bg-success mr-2 animate-pulse"></span>
                            STDOUT LIVE
                        </span>
                        
                        <button 
                            @click="autoScroll = !autoScroll"
                            class="flex items-center space-x-2 hover:text-primary transition-colors"
                            :class="autoScroll ? 'text-accent' : 'text-secondary/50'"
                        >
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 13l-7 7-7-7m14-8l-7 7-7-7" />
                            </svg>
                            <span class="tracking-widest uppercase">{{ autoScroll ? 'Auto-scroll On' : 'Auto-scroll Off' }}</span>
                        </button>

                        <span class="opacity-70 tracking-widest">BUFFER: {{ currentLogs.length }}/500 lines</span>
                    </div>

                    <div class="flex items-center space-x-6 uppercase tracking-[0.2em] opacity-60">
                        <span>ANSI Enabled</span>
                        <span>v11.1 Protocol</span>
                    </div>
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
