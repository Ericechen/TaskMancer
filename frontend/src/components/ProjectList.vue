<script setup lang="ts">
import { useProjectStore } from '../stores/projectStore'
import ProjectCard from './ProjectCard.vue'

const store = useProjectStore()
</script>

<template>
  <div>
      <!-- Empty State -->
      <div v-if="store.projects.length === 0 && store.isConnected" class="text-center py-20 text-slate-500">
         <p class="text-lg mb-2">No projects monitored yet.</p>
         <p class="text-sm">Click "Add Projects" to scan and import your task projects.</p>
      </div>

      <!-- Grid -->
      <div v-else class="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
        <div v-for="project in store.projects" :key="project.path" class="break-inside-avoid">
            <ProjectCard :project="project" />
        </div>
      </div>
  </div>
</template>
