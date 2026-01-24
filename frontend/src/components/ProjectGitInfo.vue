// src/components/ProjectGitInfo.vue
<script setup lang="ts">
import type { Project } from '../stores/projectStore'
import ProjectLinks from './ProjectLinks.vue'

const props = defineProps<{ project: Project }>()
</script>

<template>
  <div class="flex items-center w-full gap-x-3 gap-y-1 text-[10px] font-mono flex-wrap min-h-[20px]">
    <!-- Git Info -->
    <template v-if="props.project.git && props.project.git.is_git">
      <div class="flex items-center text-primary/80">
        <svg class="w-3 h-3 mr-1 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
        </svg>
        <span>{{ props.project.git.branch }}</span>
      </div>
      <div v-if="props.project.git.sync_status && props.project.git.sync_status !== 'Not checked'"
        class="flex items-center px-1.5 py-0.25 rounded bg-surface/50 border border-border/30">
        <span :class="{
          'text-success/90': props.project.git.sync_status === 'Synced',
          'text-accent/90': props.project.git.sync_status.includes('Ahead'),
          'text-warning/90': props.project.git.sync_status.includes('Behind') || props.project.git.sync_status.includes('Diverged')
        }">{{ props.project.git.sync_status }}</span>
      </div>
      <div v-if="props.project.git.uncommitted > 0" class="text-danger flex items-center">
        <span class="w-1 h-1 rounded-full bg-danger animate-pulse mr-1"></span>
        {{ props.project.git.uncommitted }} changes
      </div>
    </template>
    
    <ProjectLinks :project="props.project" />

    <!-- Momentum (right aligned) -->
    <div v-if="props.project.momentum !== undefined" class="ml-auto flex items-center text-secondary/80"
      title="Activities (Commits) in last 7 days">
      <svg class="w-3 h-3 mr-1 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
      <span>{{ props.project.momentum }} act</span>
    </div>
  </div>
</template>
