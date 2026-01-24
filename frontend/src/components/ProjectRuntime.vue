<script setup lang="ts">
import type { Project } from '../stores/projectStore'
import { useProjectStore } from '../stores/projectStore'

const props = defineProps<{ project: Project }>()
const projectStore = useProjectStore()
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
            ? 'bg-success/10 border-success/30 text-success'
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
    <div v-if="props.project.depends_on?.length" class="flex items-center flex-wrap gap-1.5">
      <div
        v-for="dep in props.project.depends_on"
        :key="dep"
        class="flex items-center space-x-1 px-1.5 py-0.5 rounded border border-white/5 bg-white/[0.02]"
        :title="`Dependency: ${dep}`"
      >
        <svg class="w-2.5 h-2.5 text-secondary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
        </svg>
        <span
          class="w-1 h-1 rounded-full"
          :class="projectStore.projects.find(p => p.name === dep || p.path.toLowerCase().replace(/\\/g, '/') === dep.toLowerCase().replace(/\\/g, '/'))?.process?.is_running ? 'bg-accent/80 shadow-[0_0_5px_rgba(139,92,246,0.5)]' : 'bg-secondary/20'"
        ></span>
        <span class="text-[9px] font-bold text-secondary/80">{{ dep }}</span>
      </div>
    </div>
  </div>
</template>
