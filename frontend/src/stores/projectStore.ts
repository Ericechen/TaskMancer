import { defineStore } from 'pinia'
import { ref } from 'vue'

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
  hasConfig: boolean;
  hasStartBat: boolean;
  hasReadme: boolean;
  git?: GitSnapshot;
  momentum?: number;
  health?: ProjectHealth;
  metrics?: CodebaseMetrics;
  live?: LiveStatus;
  process?: {
    is_running: boolean;
    stats?: { cpu: number; ram: number } | null;
    has_error: boolean;
  };
  isExpanded?: boolean;
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const isConnected = ref(false)
  const discoveryRoot = ref('')
  const searchQuery = ref('')
  const projectLogs = ref<Record<string, string[]>>({}) // path -> log lines
  const layoutMode = ref<'list' | 'grid' | 'monitor'>('list')
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
        projects.value = data.projects
      } else if (data.type === 'log') {
        const path = data.path
        if (path) {
            console.log(`[Log Stream] ${data.project}: ${data.content}`);
            if (!projectLogs.value[path]) {
              projectLogs.value[path] = []
            }
            projectLogs.value[path].push(data.content)
            // Keep last 500 lines
            if (projectLogs.value[path] && projectLogs.value[path].length > 500) {
              projectLogs.value[path].shift()
            }
        }
      } else if (data.type === 'log_status') {
          console.log(`Process for ${data.project} ${data.status}`)
          const index = projects.value.findIndex(p => p.path === data.path)
          if (index !== -1) {
            const project = { ...projects.value[index] } as any
            if (!project.process) {
                project.process = { is_running: false, stats: null, has_error: false }
            }
            project.process.is_running = data.status === 'started' || data.status === 'running'
            if (data.status === 'stopped') {
                project.process.is_running = false
                project.process.stats = null
            }
            projects.value[index] = project as any
          }
      } else if (data.type === 'process_stats') {
        const index = projects.value.findIndex(p => p.path === data.path)
        if (index !== -1) {
          const project = { ...projects.value[index] } as any
          if (!project.process) {
              project.process = { is_running: true, stats: data.stats, has_error: false }
          } else {
              project.process.stats = data.stats
              project.process.is_running = true
          }
          projects.value[index] = project as any
        }
      } else if (data.type === 'process_error') {
        const index = projects.value.findIndex(p => p.path === data.path)
        if (index !== -1) {
          const project = { ...projects.value[index] } as any
          if (!project.process) {
              project.process = { is_running: true, stats: null, has_error: data.has_error }
          } else {
              project.process.has_error = data.has_error
          }
          projects.value[index] = project as any
        }
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
    if (retryTimer) clearTimeout(retryTimer)
    retryTimer = window.setTimeout(() => {
      connect()
    }, 3000)
  }

  async function fetchConfig() {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/config')
      const data = await response.json()
      discoveryRoot.value = data.discovery_root
    } catch (e) {
      console.error('Failed to fetch config', e)
    }
  }

  async function addProject(path: string) {
    const response = await fetch('http://127.0.0.1:8000/api/roots', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    })
    if (!response.ok) throw new Error(await response.text())
  }

  async function removeProject(path: string, deleteFiles: boolean = false) {
    const response = await fetch(`http://127.0.0.1:8000/api/roots?path=${encodeURIComponent(path)}&delete_files=${deleteFiles}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error(await response.text())
  }

  async function executeAction(action: string, path: string) {
    // Clear logs when starting a new session
    if (action === 'start.bat') {
        projectLogs.value[path] = []
    }

    // [v10.4] Optimistic UI Update: immediately mark as not running if stopping
    if (action === 'stop') {
        const index = projects.value.findIndex(p => p.path === path)
        if (index !== -1) {
            const project = { ...projects.value[index] }
            if (project.process) {
                project.process.is_running = false
                project.process.stats = null
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
        formData.append('files', file)
      }
    }

    const response = await fetch('http://127.0.0.1:8000/api/projects/upload', {
      method: 'POST',
      body: formData
    })
    if (!response.ok) throw new Error(await response.text())
  }

  async function discoverProjects(path: string) {
      const response = await fetch('http://127.0.0.1:8000/api/discover', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path })
      })
      if (!response.ok) throw new Error(await response.text())
      const data = await response.json()
      return data.projects
  }

  async function createProject(parent_path: string, name: string, task_file: File | null) {
      const formData = new FormData()
      formData.append('path', parent_path)
      formData.append('name', name)
      if (task_file instanceof File) {
          formData.append('task_file', task_file)
      }

      const response = await fetch('http://127.0.0.1:8000/api/projects/create', {
          method: 'POST',
          body: formData
      })
      if (!response.ok) throw new Error(await response.text())
  }

  return {
    projects,
    isConnected,
    discoveryRoot,
    searchQuery,
    projectLogs,
    layoutMode,
    connect,
    fetchConfig,
    addProject,
    removeProject,
    executeAction,
    uploadFiles,
    discoverProjects,
    createProject
  }
})
