<script setup lang="ts">
import { computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import ProjectCard from './ProjectCard.vue'

const store = useProjectStore()

// Categories
const draftProjects = computed(() => store.projects.filter(p => p.stats.percentage === 0))
const activeProjects = computed(() => store.projects.filter(p => p.stats.percentage > 0 && p.stats.percentage < 100))
const completedProjects = computed(() => store.projects.filter(p => p.stats.percentage === 100))
</script>

<template>
  <div class="space-y-16">
      <!-- Empty State -->
      <div v-if="store.projects.length === 0 && store.isConnected" class="text-center py-20">
         <p class="text-lg mb-2 font-display text-primary">No projects monitored yet.</p>
         <p class="text-sm text-secondary">Click "Add Source" to scan and import your task projects.</p>
      </div>

      <div v-else class="space-y-16 animate-fade-in-up">
          
          <!-- Section 1: In Progress -->
          <section>
              <div class="flex items-center space-x-4 mb-6">
                  <h2 class="text-xl font-display font-bold text-primary">In Progress</h2>
                  <div class="h-[1px] flex-1 bg-accent/30"></div>
                  <span class="text-xs font-mono text-accent px-2 py-1 bg-accent/5 border border-accent/20 rounded font-bold">{{ activeProjects.length }}</span>
              </div>
              
              <div v-if="activeProjects.length === 0" class="py-12 border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-secondary">
                  <p class="font-mono text-sm opacity-50">No active projects. Start something!</p>
              </div>
              <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <ProjectCard v-for="p in activeProjects" :key="p.path" :project="p" />
              </div>
          </section>

          <!-- Section 2: Drafts (Not Started) -->
          <section v-if="draftProjects.length > 0">
              <div class="flex items-center space-x-4 mb-6">
                  <h2 class="text-xl font-display font-medium text-secondary">Drafts</h2>
                  <div class="h-[1px] flex-1 bg-border/50"></div>
                  <span class="text-xs font-mono text-secondary px-2 py-1 bg-surface border border-border rounded">{{ draftProjects.length }}</span>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <ProjectCard v-for="p in draftProjects" :key="p.path" :project="p" />
              </div>
          </section>
          
          <!-- Section 3: Completed -->
          <section v-if="completedProjects.length > 0" class="opacity-80 hover:opacity-100 transition-opacity">
               <div class="flex items-center space-x-4 mb-6">
                  <h2 class="text-xl font-display font-medium text-success">Completed</h2>
                  <div class="h-[1px] flex-1 bg-success/30"></div>
                  <span class="text-xs font-mono text-success px-2 py-1 bg-success/5 border border-success/20 rounded">{{ completedProjects.length }}</span>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <ProjectCard v-for="p in completedProjects" :key="p.path" :project="p" />
              </div>
          </section>

      </div>
  </div>
</template>
