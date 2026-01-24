<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import AnsiUp from 'ansi-to-html'

const props = defineProps<{
    project: any
    logs: string[]
}>()

const emit = defineEmits(['action'])
const logContainer = ref<HTMLElement | null>(null)

const ansi = new AnsiUp({
    fg: '#F8FAFC',
    bg: 'transparent',
    newline: false,
    escapeXML: true,
})

function parseAnsi(text: string) {
    return ansi.toHtml(text)
}

function scrollToBottom() {
    if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
}

// Watch for log changes to auto-scroll
watch(() => props.logs.length, () => {
    nextTick(scrollToBottom)
})

// Scroll to bottom on initial mount
onMounted(() => {
    nextTick(scrollToBottom)
})
</script>

<template>
    <div class="bg-[#0a0a0a]/90 backdrop-blur-3xl border border-white/5 rounded-3xl overflow-hidden flex flex-col h-[500px] shadow-2xl ring-1 ring-white/[0.03]">
        <!-- Monitor Header (Compact) -->
        <div class="px-8 py-4 border-b border-white/5 bg-white/[0.01] flex items-center justify-between">
            <div class="flex items-center space-x-4">
                <div class="relative flex items-center justify-center">
                    <span class="absolute w-3 h-3 rounded-full bg-success opacity-20 animate-ping"></span>
                    <span class="relative w-2 h-2 rounded-full bg-success"></span>
                </div>
                <h3 class="text-sm font-black text-primary font-mono tracking-tighter uppercase">{{ project.name }}</h3>
                <span class="text-[9px] text-secondary font-mono opacity-70 truncate max-w-md hidden md:block">{{ project.path }}</span>
            </div>

            <!-- Controls -->
            <div class="flex items-center space-x-6">
                <div class="flex items-center space-x-4 font-mono text-[10px]">
                    <div class="flex items-center space-x-2">
                        <span class="text-secondary opacity-70 uppercase tracking-widest">CPU</span>
                        <span class="text-accent font-bold">{{ project.process?.stats?.cpu }}%</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="text-secondary opacity-70 uppercase tracking-widest">RAM</span>
                        <span class="text-success font-bold">{{ project.process?.stats?.ram }} MB</span>
                    </div>
                </div>
                
                <div class="h-4 w-[1px] bg-white/10"></div>

                <div class="flex items-center space-x-2 bg-void/40 rounded-xl p-1 border border-white/5">
                    <button 
                        @click="$emit('action', 'start.bat', project.path)"
                        class="p-2 hover:bg-white/5 hover:text-accent transition-all rounded-lg text-secondary"
                        title="Restart Instance"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                    <button 
                        @click="$emit('action', 'stop', project.path)"
                        class="p-2 hover:bg-danger/20 hover:text-danger transition-all rounded-lg text-secondary"
                        title="Kill Instance"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <!-- Split Content: Log Left, Performance Right -->
        <div class="flex-1 flex overflow-hidden">
            <!-- Left: Terminal Stream (70%) -->
            <div class="w-2/3 border-r border-white/5 bg-black/20 flex flex-col">
                <div class="px-6 py-2 bg-white/[0.02] border-b border-white/5 flex items-center space-x-2">
                    <div class="w-2 h-2 rounded-full bg-rose-500/20"></div>
                    <span class="text-[8px] font-black uppercase tracking-widest text-secondary/60">Live Terminal Stream</span>
                </div>
                <div 
                    ref="logContainer"
                    class="flex-1 overflow-y-auto p-6 font-mono text-[11px] space-y-1.5 custom-scrollbar"
                >
                    <div v-if="!logs.length" class="h-full flex items-center justify-center text-zinc-600 italic text-xs animate-pulse">Waiting for initial output...</div>
                    <div v-for="(line, idx) in logs" :key="idx" class="flex group">
                        <span class="text-zinc-700 mr-4 select-none w-6 text-right font-bold opacity-60 group-hover:opacity-100 transition-opacity">{{ idx + 1 }}</span>
                        <span class="text-zinc-300 break-all whitespace-pre-wrap leading-relaxed" v-html="parseAnsi(line)"></span>
                    </div>
                </div>
            </div>

            <!-- Right: Performance Metrics Area (30%) -->
            <div class="w-1/3 bg-void/20 p-8 flex flex-col space-y-10 overflow-y-auto custom-scrollbar">
                <!-- CPU Mini Area -->
                <div>
                    <div class="flex items-center justify-between mb-4">
                        <span class="text-[9px] font-black uppercase tracking-widest text-accent">CPU Usage Trend</span>
                        <span class="text-lg font-mono font-bold text-primary">{{ project.process?.stats?.cpu }}%</span>
                    </div>
                    <div class="h-24 w-full bg-black/40 rounded-xl border border-white/5 relative overflow-hidden">
                        <svg 
                            v-if="project.process?.history?.cpu?.length" 
                            class="w-full h-full" 
                            viewBox="0 0 300 100" 
                            preserveAspectRatio="none"
                        >
                                <polyline 
                                fill="none" 
                                stroke="#8B5CF6" 
                                stroke-width="2" 
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                :points="project.process.history.cpu.map((v: number, i: number) => `${i * (300/299)},${100 - (v / 100) * 100}`).join(' ')" 
                                class="drop-shadow-[0_0_8px_rgba(139,92,246,0.3)]"
                            />
                        </svg>
                        <div v-else class="absolute inset-0 flex items-center justify-center text-[8px] text-secondary font-mono opacity-50 italic">Sampling...</div>
                    </div>
                </div>

                <!-- RAM Mini Area -->
                <div>
                    <div class="flex items-center justify-between mb-4">
                        <span class="text-[9px] font-black uppercase tracking-widest text-success">Memory Trend</span>
                        <span class="text-lg font-mono font-bold text-primary">{{ project.process?.stats?.ram }} <span class="text-[10px] text-secondary">MB</span></span>
                    </div>
                    <div class="h-24 w-full bg-black/40 rounded-xl border border-white/5 relative overflow-hidden">
                        <svg 
                            v-if="project.process?.history?.ram?.length" 
                            class="w-full h-full" 
                            viewBox="0 0 300 100" 
                            preserveAspectRatio="none"
                        >
                                <polyline 
                                fill="none" 
                                stroke="#10B981" 
                                stroke-width="2" 
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                :points="project.process.history.ram.map((v: number, i: number) => `${i * (300/299)},${100 - (v / Math.max(...project.process.history.ram, 512)) * 100}`).join(' ')" 
                                class="drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]"
                            />
                        </svg>
                        <div v-else class="absolute inset-0 flex items-center justify-center text-[8px] text-secondary font-mono opacity-50 italic">Sampling...</div>
                    </div>
                </div>

                <div class="pt-6 border-t border-white/5 space-y-4">
                    <div class="text-[9px] font-black uppercase tracking-tighter text-secondary/70">Technical Stack</div>
                    <div class="flex flex-wrap gap-2">
                        <span v-for="tag in project.tags" :key="tag" class="px-2.5 py-1 bg-white/[0.03] text-primary text-[8px] font-bold uppercase tracking-widest rounded border border-white/5">
                            {{ tag }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
