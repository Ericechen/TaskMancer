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
        { label: 'Pending', value: pending, color: '#2A2A2A' }, // Border color (subtle)
        { label: 'In Progress', value: inProgress, color: '#8B5CF6' }, // Accent
        { label: 'Done', value: done, color: '#10B981' } // Success
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
  <div class="space-y-12">
    <!-- Top Stats Cards (Minimalist) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-border/50">
        <div class="group">
            <h3 class="text-secondary text-[10px] font-bold uppercase tracking-widest mb-1 group-hover:text-accent transition-colors">Total Projects</h3>
            <div class="flex items-baseline space-x-2">
                <span class="text-6xl font-display font-light text-primary">{{ totalProjects }}</span>
                <span class="text-sm font-mono text-secondary">Active</span>
            </div>
            <div class="mt-2 text-xs text-secondary font-mono">
                <span class="text-accent">{{ totalTasks }}</span> Tasks tracked
            </div>
        </div>

        <div class="group">
            <h3 class="text-secondary text-[10px] font-bold uppercase tracking-widest mb-1 group-hover:text-accent transition-colors">Completion Rate</h3>
            <div class="flex items-baseline space-x-2">
                <span class="text-6xl font-display font-light" :class="globalProgress === 100 ? 'text-success' : 'text-primary'">{{ globalProgress }}%</span>
            </div>
             <div class="w-24 bg-surface rounded-full h-1 mt-4 overflow-hidden">
                <div 
                    class="h-full rounded-full transition-all duration-1000 ease-out"
                    :class="globalProgress === 100 ? 'bg-success' : 'bg-accent'"
                    :style="{ width: `${globalProgress}%` }"
                ></div>
            </div>
        </div>
        
         <div class="group relative overflow-hidden">
             <div class="z-10 relative">
                 <h3 class="text-secondary text-[10px] font-bold uppercase tracking-widest mb-1 group-hover:text-accent transition-colors">Productivity Pulse</h3>
                 <div class="text-6xl font-display font-light text-primary tracking-tighter">{{ completedTasks }}</div>
                 <p class="text-xs text-secondary font-mono mt-2">
                     Tasks completed across the board.
                 </p>
             </div>
             <div class="absolute right-0 top-0 text-6xl opacity-10 grayscale group-hover:grayscale-0 transition-all duration-500">🚀</div>
         </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
        <!-- Chart Section -->
        <div class="flex flex-col items-center justify-center p-8 border border-border rounded-2xl bg-surface/30 relative">
            <div class="absolute top-6 left-6">
                <h3 class="text-primary font-display font-bold text-lg">Project Status</h3>
                <p class="text-xs text-secondary font-mono tracking-wide">Distribution Overview</p>
            </div>
            <DonutChart :items="projectStatus" :size="240" :stroke-width="12" />
        </div>

        <div class="flex flex-col space-y-8">
            <!-- Focus List -->
            <div class="flex-1">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-primary font-display font-bold text-lg">Needs Focus</h3>
                    <span class="text-[10px] text-secondary border border-border px-2 py-1 rounded font-mono">Most Remaining</span>
                </div>
                
                <div v-if="focusProjects.length === 0" class="text-secondary text-sm py-4 italic font-mono">No critical items. All clear.</div>
                <div v-else class="space-y-4">
                    <div v-for="proj in focusProjects" :key="proj.path" class="flex justify-between items-center group py-2 border-b border-border/50 hover:border-accent/50 transition-colors cursor-default">
                        <div class="min-w-0 pr-4">
                            <div class="font-display font-medium text-primary text-lg group-hover:text-accent transition-colors truncate">{{ proj.name }}</div>
                            <div class="text-[10px] text-secondary font-mono truncate opacity-60">{{ proj.path }}</div>
                        </div>
                        <div class="text-right flex-shrink-0">
                             <div class="text-2xl font-display font-light text-primary group-hover:text-danger conversion-colors">
                                 {{ proj.stats.total - proj.stats.completed }}
                             </div>
                             <div class="text-[10px] text-secondary uppercase tracking-widest">Left</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Wins -->
            <div class="flex-1 pt-8 border-t border-border/50">
                <div class="flex justify-between items-center mb-6">
                     <h3 class="text-primary font-display font-bold text-lg">Quick Wins</h3>
                     <span class="text-[10px] text-accent border border-accent/30 bg-accent/5 px-2 py-1 rounded font-mono">>75% Done</span>
                </div>
                
                <div v-if="quickWins.length === 0" class="text-secondary text-sm py-4 italic font-mono">No sprints available.</div>
                <div v-else class="space-y-4">
                    <div v-for="proj in quickWins" :key="proj.path" class="group cursor-default">
                        <div class="flex justify-between items-end mb-2">
                             <div class="font-display font-medium text-primary text-sm">{{ proj.name }}</div>
                             <div class="text-xs font-mono font-bold text-success">{{ proj.stats.percentage }}%</div>
                        </div>
                        <div class="w-full bg-border rounded-full h-0.5 overflow-hidden group-hover:h-1 transition-all duration-300">
                            <div class="h-full bg-success rounded-full" :style="{ width: `${proj.stats.percentage}%` }"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>
