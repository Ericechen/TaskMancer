<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useProjectStore } from '../stores/projectStore';
import { VueFlow, useVueFlow } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import '@vue-flow/core/dist/style.css';
import '@vue-flow/controls/dist/style.css';

const store = useProjectStore();

const { fitView } = useVueFlow();

const nodes = ref<any[]>([]);
const edges = ref<any[]>([]);

// 轉換 Project Data 為 Vue Flow 格式
const updateGraph = () => {
    if (!store.projects || store.projects.length === 0) return;

    const newNodes: any[] = [];
    const newEdges: any[] = [];
    
    // 簡單的自動佈局 (未來可以用 dagre 優化)
    // 這裡先簡單用網格排列
    const GRID_COLS = 3;
    const GRID_X = 250;
    const GRID_Y = 150;

    store.projects.forEach((proj, index) => {
        // Node Status Color
        let statusColor = '#64748b'; // default slate-500
        if (proj.process?.is_running) {
            statusColor = '#22c55e'; // green-500
            if (proj.process?.has_error) statusColor = '#ef4444'; // red-500
        }

        newNodes.push({
            id: proj.name, // 使用專案名稱作為 ID
            type: 'default',
            data: { label: proj.name, path: proj.path },
            position: { 
                x: (index % GRID_COLS) * GRID_X, 
                y: Math.floor(index / GRID_COLS) * GRID_Y 
            },
            style: { 
                background: '#1e293b', 
                color: '#fff', 
                border: `2px solid ${statusColor}`,
                borderRadius: '8px',
                padding: '10px',
                width: '180px',
                textAlign: 'center'
            }
        });

        // 建立 Edges (依賴關係)
        if (proj.depends_on && proj.depends_on.length > 0) {
            proj.depends_on.forEach(depName => {
                newEdges.push({
                    id: `e-${proj.name}-${depName}`,
                    source: proj.name, // 上游 (依賴方) -> 實際執行邏輯是 A 依賴 B，所以箭頭應該 B -> A 還是 A -> B?
                    // 通常「依賴圖」箭頭指向依賴對象：A -> B (A depends on B)
                    target: depName,
                    animated: true,
                    style: { stroke: '#94a3b8' }
                });
            });
        }
    });

    nodes.value = newNodes;
    edges.value = newEdges;
    
    // [Feature Request] Don't auto-fit view on updates to preserve user's zoom/pan state
    // setTimeout(() => {
    //     fitView();
    // }, 100);
};

// 監聽 Store 變化
// [Performance Optimization]
// 創建一個 Computed Projection，只包含影響圖表外觀的屬性。
// 這樣可以過濾掉 store 中頻繁變動的 CPU/RAM 數據，避免觸發不必要的圖表重繪。
const graphState = computed(() => {
    return store.projects.map(p => ({
        name: p.name,
        path: p.path,
        depends_on: p.depends_on,
        isRunning: p.process?.is_running,
        hasError: p.process?.has_error
    }));
});

// 監聽 Store 變化 (只更新節點狀態，不重置 Viewport)
watch(graphState, () => {
    updateGraph();
}, { deep: true, immediate: true });

// 首次加載時自動適應視野
onMounted(() => {
    updateGraph();
    setTimeout(() => {
        fitView();
    }, 200);
});

const onNodeClick = (event: any) => {
    console.log('Node clicked:', event.node);
    // 未來可以做跳轉或開啟詳情
};

</script>

<template>
  <div class="h-full w-full bg-slate-900 rounded-lg shadow-lg border border-slate-700 overflow-hidden">
    <div class="p-4 border-b border-slate-700 bg-slate-800 flex justify-between items-center">
        <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <span class="text-indigo-400">⚡</span> 專案依賴關係圖
        </h2>
        <div class="text-sm text-slate-400">
            <span class="inline-block w-2 h-2 rounded-full bg-green-500 mr-1"></span>運作中
            <span class="inline-block w-2 h-2 rounded-full bg-slate-500 ml-2 mr-1"></span>停止
            <span class="inline-block w-2 h-2 rounded-full bg-red-500 ml-2 mr-1"></span>錯誤
        </div>
    </div>
    
    <div class="h-[500px]">
        <VueFlow
            v-model:nodes="nodes"
            v-model:edges="edges"
            class="basic-flow"
            :default-zoom="1.5"
            :min-zoom="0.2"
            :max-zoom="4"
            fit-view-on-init
            @node-click="onNodeClick"
        >
            <Background pattern-color="#334155" :gap="8" />
            <Controls />
        </VueFlow>
    </div>
  </div>
</template>

<style>
/* Vue Flow Dark Theme Override */
.vue-flow__node-default {
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}
.vue-flow__metrics {
    color: #fff;
}
</style>
