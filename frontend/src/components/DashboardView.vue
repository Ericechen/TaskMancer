<script setup lang="ts">
import { computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import DonutChart from './DonutChart.vue'

const store = useProjectStore()

// Aggregated Stats
const totalProjects = computed(() => store.projects.length)
const totalTasks = computed(() => store.projects.reduce((sum, p) => sum + p.stats.total, 0))
const completedTasks = computed(() => store.projects.reduce((sum, p) => sum + p.stats.completed, 0))
const globalProgress = computed(() => {
    if (totalTasks.value === 0) return 0
    return Math.round((completedTasks.value / totalTasks.value) * 100)
})

// Project Status Distribution
const projectStatus = computed(() => {
    const pending = store.projects.filter(p => p.stats.percentage === 0).length
    const done = store.projects.filter(p => p.stats.percentage === 100).length
    const inProgress = totalProjects.value - pending - done
    
    return [
        { label: 'Pending', value: pending, color: '#94a3b8' }, // Slate 400
        { label: 'In Progress', value: inProgress, color: '#0ea5e9' }, // Sky 500
        { label: 'Done', value: done, color: '#10b981' } // Emerald 500
    ]
})

// Top Projects Needing Focus (Most remaining tasks)
const focusProjects = computed(() => {
    return [...store.projects]
        .filter(p => p.stats.percentage < 100) // Only incomplete projects
        .sort((a, b) => (b.stats.total - b.stats.completed) - (a.stats.total - a.stats.completed))
        .slice(0, 3)
})

// Quick Wins (Projects > 75% complete but not done)
const quickWins = computed(() => {
    return store.projects
        .filter(p => p.stats.percentage >= 75 && p.stats.percentage < 100)
        .sort((a, b) => b.stats.percentage - a.stats.percentage)
        .slice(0, 3)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Top Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg">
            <h3 class="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Total Statistics</h3>
            <div class="flex items-baseline space-x-2">
                <span class="text-3xl font-bold text-white">{{ totalProjects }}</span>
                <span class="text-xs text-slate-500">Projects</span>
            </div>
            <div class="mt-2 text-xs text-slate-400">
                <span class="text-sky-400 font-bold">{{ totalTasks }}</span> Tasks tracked
            </div>
        </div>

        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg">
            <h3 class="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Global Completion</h3>
            <div class="flex items-baseline space-x-2">
                <span class="text-3xl font-bold" :class="globalProgress === 100 ? 'text-emerald-400' : 'text-sky-400'">{{ globalProgress }}%</span>
                <span class="text-xs text-slate-500">Done</span>
            </div>
             <div class="w-full bg-slate-700 rounded-full h-1.5 mt-3 overflow-hidden">
                <div 
                    class="h-full rounded-full transition-all duration-500 ease-out"
                    :class="globalProgress === 100 ? 'bg-emerald-500' : 'bg-sky-500'"
                    :style="{ width: `${globalProgress}%` }"
                ></div>
            </div>
        </div>
        
         <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg flex items-center justify-between relative overflow-hidden">
             <!-- Decorative bg -->
             <div class="absolute -right-6 -bottom-6 w-24 h-24 bg-indigo-500/10 rounded-full blur-xl"></div>
             
             <div class="z-10">
                 <h3 class="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Productivity Pulse</h3>
                 <p class="text-xs text-slate-400 leading-relaxed max-w-[150px]">
                     You have completed <strong class="text-emerald-400">{{ completedTasks }}</strong> tasks across all projects.
                 </p>
             </div>
             <div class="text-3xl">🚀</div>
         </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Chart Section -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg flex flex-col items-center justify-center">
            <h3 class="text-slate-200 font-bold mb-6 self-start w-full border-b border-slate-700 pb-2">Project Status</h3>
            <DonutChart :items="projectStatus" :size="180" :stroke-width="20" />
        </div>

        <div class="flex flex-col space-y-6">
            <!-- Focus List -->
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg flex-1">
                <h3 class="text-slate-200 font-bold mb-4 border-b border-slate-700 pb-2">Needs Focus (Most Remaining Tests)</h3>
                <div v-if="focusProjects.length === 0" class="text-slate-500 text-sm py-4">All tracked projects fully completed! 🎉</div>
                <div v-else class="space-y-3">
                    <div v-for="proj in focusProjects" :key="proj.path" class="flex justify-between items-center p-3 rounded-lg bg-slate-900/50 border border-slate-700/50 hover:border-slate-600 transition-colors">
                        <div class="min-w-0 pr-2">
                            <div class="font-medium text-slate-200 truncate">{{ proj.name }}</div>
                            <div class="text-xs text-slate-500 truncate">{{ proj.path }}</div>
                        </div>
                        <div class="text-right flex-shrink-0">
                             <div class="text-xs font-bold text-rose-400">
                                 {{ proj.stats.total - proj.stats.completed }} Left
                             </div>
                             <div class="text-[10px] text-slate-500">
                                 {{ proj.stats.percentage }}%
                             </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Wins -->
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg flex-1">
                <div class="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
                    <h3 class="text-slate-200 font-bold">Quick Wins ⚡</h3>
                    <span class="text-[10px] text-sky-400 font-mono bg-sky-900/30 px-2 py-0.5 rounded">>75% Done</span>
                </div>
                
                <div v-if="quickWins.length === 0" class="text-slate-500 text-sm py-4">No projects in the final stretch. Keep pushing!</div>
                <div v-else class="space-y-3">
                    <div v-for="proj in quickWins" :key="proj.path" class="p-3 rounded-lg bg-slate-900/50 border border-slate-700/50 hover:border-slate-600 transition-colors">
                        <div class="flex justify-between items-center mb-2">
                             <div class="font-medium text-slate-200 text-sm truncate">{{ proj.name }}</div>
                             <div class="text-xs font-bold text-emerald-400">{{ proj.stats.percentage }}%</div>
                        </div>
                        <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div class="h-full bg-emerald-500 rounded-full" :style="{ width: `${proj.stats.percentage}%` }"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>
