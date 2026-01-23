<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  size?: number
  strokeWidth?: number
  items: { color: string; value: number; label: string }[]
}>()

const size = props.size || 150
const strokeWidth = props.strokeWidth || 15
const radius = (size - strokeWidth) / 2
const circumference = 2 * Math.PI * radius

const total = computed(() => props.items.reduce((sum, item) => sum + item.value, 0))

const segments = computed(() => {
  let accumulatedOffset = 0
  return props.items.map(item => {
    const percentage = total.value === 0 ? 0 : item.value / total.value
    const dashArray = `${percentage * circumference} ${circumference}`
    const offset = accumulatedOffset
    accumulatedOffset -= percentage * circumference
    return {
      ...item,
      dashArray,
      offset,
      percentage: Math.round(percentage * 100)
    }
  })
})
</script>

<template>
  <div class="relative flex flex-col items-center">
    <svg :width="size" :height="size" class="rotate-[-90deg]">
      <template v-if="total > 0">
          <circle
            v-for="(seg, index) in segments"
            :key="index"
            :r="radius"
            :cx="size / 2"
            :cy="size / 2"
            fill="transparent"
            :stroke="seg.color"
            :stroke-width="strokeWidth"
            :stroke-dasharray="seg.dashArray"
            :stroke-dashoffset="seg.offset"
            class="transition-all duration-1000 ease-out"
          />
      </template>
      <circle
        v-else
        :r="radius"
        :cx="size / 2"
        :cy="size / 2"
        fill="transparent"
        stroke="#334155"
        :stroke-width="strokeWidth"
        class="opacity-50"
      />
    </svg>
    
    <!-- Legend -->
    <div class="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
        <div v-for="item in segments" :key="item.label" class="flex items-center space-x-2">
            <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: item.color }"></span>
            <span class="text-slate-300">{{ item.label }} ({{ item.value }})</span>
        </div>
    </div>
  </div>
</template>
