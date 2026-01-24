import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Task {
  text: string;
  status: 'todo' | 'done';
  level: number;
  children: Task[];
}

export interface ProjectStats {
  total: number;
  completed: number;
  percentage: number;
}

export interface GitSnapshot {
  branch: string;
  is_git: boolean;
  uncommitted: number;
  sync_status: string;
}

export interface ProjectHealth {
  has_node_modules: boolean;
  has_venv: boolean;
  is_npm: boolean;
  is_python: boolean;
}

export interface CodebaseMetrics {
  loc: number;
  languages: Record<string, number>;
  fileCount: number;
  size: number;
}

export interface LiveStatus {
  active_ports: { port: number; label?: string; status: 'online' | 'offline' }[];
  dependency_audit: {
    status: string;
    dep_count?: number;
    dev_dep_count?: number;
    total_count?: number;
    has_package_lock?: boolean;
    message?: string;
  };
}

export interface Project {
  name: string;
  path: string;
  stats: ProjectStats;
  tasks: Task[];
  links: string[];
  depends_on: string[];
  hasConfig: boolean;
  hasStartBat: boolean;
  hasReadme: boolean;
  tags: string[];
  git?: GitSnapshot;
  momentum?: number;
  health?: ProjectHealth;
  metrics?: CodebaseMetrics;
  live?: LiveStatus;
  process?: {
    is_running: boolean;
    stats?: { cpu: number; ram: number } | null;
    history?: { cpu: number[]; ram: number[] };
    has_error: boolean;
    alert_level?: 'normal' | 'warning' | 'critical';
  };
  isExpanded?: boolean;
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const isConnected = ref(false)
  const discoveryRoot = ref('')
  const searchQuery = ref('')
  const selectedTag = ref('')
  const projectLogs = ref<Record<string, string[]>>({}) // path -> log lines
  const layoutMode = ref<'list' | 'grid' | 'monitor'>('list')
  const totalSystemRamMb = ref(16384) // Placeholder, updated on connect
  
  // [v11.2] Reactive Global Aggregator
  const globalMetrics = computed(() => {
    let cpu = 0
    let ramMb = 0
    let activeCount = 0
    
    projects.value.forEach(p => {
        if (p.process?.is_running && p.process?.stats) {
            cpu += p.process.stats.cpu
            ramMb += p.process.stats.ram
            activeCount++
        }
    })
    
    return {
        cpu_percent: cpu.toFixed(1),
        ram_used_gb: (ramMb / 1024).toFixed(2),
        ram_percent: ((ramMb / totalSystemRamMb.value) * 100).toFixed(2),
        ram_total_gb: (totalSystemRamMb.value / 1024).toFixed(1),
        count: activeCount
    }
  })
  let socket: WebSocket | null = null
  let retryTimer: number | null = null

  function connect() {
    if (socket) return

    socket = new WebSocket('ws://127.0.0.1:8000/ws')

    socket.onopen = () => {
      console.log('Connected to TaskMancer Backend')
      isConnected.value = true
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.projects) {
        projects.value = data.projects.map((p: any) => ({
            ...p,
            path: p.path.toLowerCase().replace(/\\/g, '/') // [v11.2] Standardize
        }))
        if (data.system) {
            // Update total capacity one time or periodically
            totalSystemRamMb.value = data.system.ram_total_gb * 1024
        }
      } else if (data.type === 'log') {
        const path = data.path?.toLowerCase().replace(/\\/g, '/')
        if (path) {
            if (!projectLogs.value[path]) {
                projectLogs.value[path] = []
            }
            projectLogs.value[path].push(data.content)
            if (projectLogs.value[path].length > 500) {
                projectLogs.value[path].shift()
            }
        }
      } else if (data.type === 'log_status') {
          const index = projects.value.findIndex(p => p.path.toLowerCase() === data.path.toLowerCase())
          if (index !== -1) {
            const project = { ...projects.value[index] } as any
            if (!project.process) {
                project.process = { is_running: false, stats: null, has_error: false }
            }
            project.process.is_running = data.status === 'started' || data.status === 'running'
            if (data.status === 'stopped') {
                project.process.is_running = false
                project.process.stats = null
                project.process.history = undefined
            }
            projects.value[index] = project as any
          }
      } else if (data.type === 'process_stats') {
        const path = data.path?.toLowerCase().replace(/\\/g, '/')
        const index = projects.value.findIndex(p => p.path === path)
        if (index !== -1) {
          const project = { ...projects.value[index] } as any
          if (!project.process) {
              project.process = { is_running: true, stats: data.stats, has_error: false, history: data.history }
          } else {
              project.process.stats = data.stats
              project.process.is_running = true
              project.process.history = data.history
          }
          projects.value[index] = project as any
        }
      } else if (data.type === 'process_error') {
        const path = data.path?.toLowerCase().replace(/\\/g, '/')
        const index = projects.value.findIndex(p => p.path === path)
        if (index !== -1) {
          const project = { ...projects.value[index] } as any
          if (!project.process) {
              project.process = { is_running: true, stats: null, has_error: data.has_error }
          } else {
              project.process.has_error = data.has_error
          }
          projects.value[index] = project as any
        }
      } else if (data.type === 'project_patch') {
          // [v12.0] Delta Update
          const p = data.project
          const path = p.path.toLowerCase().replace(/\\/g, '/')
          const index = projects.value.findIndex(p => p.path === path)
          if (index !== -1) {
              projects.value[index] = { ...p, path }
          } else {
              projects.value.push({ ...p, path })
          }
      } else if (data.type === 'system_stats') {
          // [v12.0] Direct system stats update
          // This will trigger globalMetrics re-computation automatically
      }
    }

    socket.onclose = () => {
      console.log('Disconnected from Backend')
      isConnected.value = false
      socket = null
      scheduleReconnect()
    }
  }

  function scheduleReconnect() {
    if (retryTimer) return
    retryTimer = window.setTimeout(() => {
      retryTimer = null
      connect()
    }, 3000)
  }

  async function fetchConfig() {
    const response = await fetch('http://127.0.0.1:8000/api/config')
    const data = await response.json()
    discoveryRoot.value = data.discovery_root
  }

  async function discoverProjects(rootPath: string) {
    const response = await fetch('http://127.0.0.1:8000/api/discover', { // Fixed Route
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: rootPath })
    })
    const data = await response.json()
    return data.projects || []
  }

  async function createProject(path: string, name: string, taskFile?: File | null) {
      const formData = new FormData()
      formData.append('path', path)
      formData.append('name', name)
      if (taskFile) {
          formData.append('task_file', taskFile as any)
      }
      const response = await fetch('http://127.0.0.1:8000/api/projects/create', {
          method: 'POST',
          body: formData
      })
      if (!response.ok) throw new Error(await response.text())
  }

  async function addProject(path: string) {
    const response = await fetch('http://127.0.0.1:8000/api/roots', { // Fixed Route (matches main.py POST /api/roots)
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    })
    if (!response.ok) throw new Error(await response.text())
  }

  async function removeProject(path: string, deleteFiles: boolean) {
    const response = await fetch(`http://127.0.0.1:8000/api/roots?path=${encodeURIComponent(path)}&delete_files=${deleteFiles}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error(await response.text())
  }

  async function executeAction(action: string, path: string) {
    const normPath = path.toLowerCase().replace(/\\/g, '/')
    if (action === 'start.bat') {
        projectLogs.value[normPath] = []
    }

    if (action === 'stop') {
        const index = projects.value.findIndex(p => p.path.toLowerCase() === path.toLowerCase())
        if (index !== -1) {
            const project = { ...projects.value[index] }
            if (project.process) {
                project.process.is_running = false
                project.process.stats = null
                project.process.history = undefined
                projects.value[index] = project as any
            }
        }
    }
    
    const response = await fetch('http://127.0.0.1:8000/api/projects/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, path })
    })
    if (!response.ok) throw new Error(await response.text())
  }

  async function uploadFiles(path: string, files: FileList) {
    const formData = new FormData()
    formData.append('path', path)
    for (let i = 0; i < files.length; i++) {
        const file = files[i]
        if (file) {
            formData.append('files', file as any)
        }
    }

    const response = await fetch('http://127.0.0.1:8000/api/projects/upload', {
      method: 'POST',
      body: formData
    })
    if (!response.ok) throw new Error(await response.text())
  }

  async function ensureLogsLoaded(path: string) {
      const normPath = path.toLowerCase().replace(/\\/g, '/')
      if (projectLogs.value[normPath] && projectLogs.value[normPath].length > 0) return
      
      try {
          const response = await fetch(`http://127.0.0.1:8000/api/projects/logs?path=${encodeURIComponent(normPath)}&limit=500`)
          const data = await response.json()
          projectLogs.value[normPath] = data.logs || []
      } catch (e) {
          console.error('Failed to load historical logs', e)
      }
  }

  return {
    projects,
    isConnected,
    discoveryRoot,
    searchQuery,
    selectedTag,
    projectLogs,
    layoutMode,
    globalMetrics,
    connect,
    fetchConfig,
    createProject,
    addProject,
    removeProject,
    executeAction,
    discoverProjects,
    uploadFiles,
    ensureLogsLoaded
  }
})
