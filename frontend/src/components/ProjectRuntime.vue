<script setup lang="ts">
import { computed } from 'vue'
import type { Project } from '../stores/projectStore'
import { useProjectStore } from '../stores/projectStore'

const props = defineProps<{ project: Project }>()
const projectStore = useProjectStore()

// Memoize dependency status lookup
const dependencies = computed(() => {
  if (!props.project.depends_on?.length) return []
  
  return props.project.depends_on.map(dep => {
    // Normalize paths for comparison
    const normDep = dep.toLowerCase().replace(/\\/g, '/')
    
    // Find the project that matches this dependency name
    const found = projectStore.projects.find(p => 
        p.name === dep || 
        p.path.toLowerCase().replace(/\\/g, '/') === normDep
    )

    return {
      name: dep,
      isRunning: !!found?.process?.is_running,
      hasError: !!found?.process?.has_error,
      alertLevel: found?.process?.alert_level,
      project: found
    }
  })
})

const handleDependencyClick = (dep: any) => {
    if (dep.project) {
        console.log(`[Dependency] ${dep.name} -> ${dep.project.path}`)
        // Future: Scroll to project or open details
    }
}
</script>

<template>
  <div class="flex items-center w-full gap-x-3 gap-y-1 mt-0.5 flex-wrap">
    <!-- Live Ports -->
    <div v-if="props.project.hasConfig && props.project.live?.active_ports?.length" class="flex items-center flex-wrap gap-1">
      <a
        v-for="item in props.project.live.active_ports"
        :key="item.port"
        :href="item.status === 'online' ? `http://localhost:${item.port}` : 'javascript:void(0)'"
        target="_blank"
        :class="[
          'flex items-center space-x-1 px-1.5 py-0.25 rounded border text-[9px] font-bold transition-all',
          item.status === 'online'
            ? 'bg-success/10 border-success/30 text-success hover:bg-success/20'
            : 'bg-void/50 border-border/50 text-secondary opacity-50 cursor-not-allowed'
        ]"
        :title="item.status === 'online' ? `Open ${item.label || 'service'} on port ${item.port}` : `${item.label || 'Service'} is offline`"
      >
        <span
          :class="['w-1.5 h-1.5 rounded-full', item.status === 'online' ? 'bg-success animate-pulse' : 'bg-void border border-secondary/30']"
        ></span>
        <span>{{ item.label || 'Live' }}: {{ item.port }}</span>
      </a>
    </div>

    <!-- Dependencies -->
    <div v-if="dependencies.length" class="flex items-center flex-wrap gap-1.5">
      <button
        v-for="dep in dependencies"
        :key="dep.name"
        @click="handleDependencyClick(dep)"
        class="flex items-center space-x-1 px-1.5 py-0.5 rounded border border-white/5 bg-white/[0.02] transition-colors hover:border-white/10 hover:bg-white/5 cursor-pointer group/dep"
        :class="{'cursor-default': !dep.project}"
        :title="dep.project ? `Dependency: ${dep.name} (${dep.isRunning ? 'Running' : 'Stopped'})` : `External Dependency: ${dep.name}`"
      >
        <svg class="w-2.5 h-2.5 text-secondary/40 group-hover/dep:text-secondary/60 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
        </svg>
        <span
          class="w-1 h-1 rounded-full transition-all"
          :class="[
            dep.isRunning 
                ? (dep.hasError ? 'bg-danger shadow-[0_0_5px_rgba(239,68,68,0.5)]' : 'bg-accent/80 shadow-[0_0_5px_rgba(139,92,246,0.5)]') 
                : 'bg-secondary/20 group-hover/dep:bg-secondary/40'
          ]"
        ></span>
        <span class="text-[9px] font-bold text-secondary/80 group-hover/dep:text-primary transition-colors">{{ dep.name }}</span>
      </button>
    </div>
  </div>
</template>
