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

export interface Project {
  name: string;
  path: string;
  stats: ProjectStats;
  tasks: Task[];
  links: string[];
  hasStartBat: boolean;
  hasReadme: boolean;
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const isConnected = ref(false)
  let socket: WebSocket | null = null
  let retryTimer: number | null = null

  function connect() {
    if (socket) return

    // Assuming backend is on localhost:8000 based on main.py
    socket = new WebSocket('ws://127.0.0.1:8000/ws')

    socket.onopen = () => {
      isConnected.value = true
      console.log('WebSocket Connected')
      if (retryTimer) {
        clearTimeout(retryTimer)
        retryTimer = null
      }
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.projects) {
          projects.value = data.projects
        }
      } catch (e) {
        console.error('Failed to parse WS message', e)
      }
    }

    socket.onclose = () => {
      isConnected.value = false
      socket = null
      console.log('WebSocket Disconnected. Retrying in 3s...')
      retryTimer = setTimeout(connect, 3000)
    }

    socket.onerror = (error) => {
      console.error('WebSocket Error', error)
      socket?.close()
    }
  }

  async function addProject(path: string) {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/roots', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path }),
      })
      if (!response.ok) {
        throw new Error('Failed to add project')
      }
      return true
    } catch (e) {
      console.error(e)
      return false
    }
  }

  async function removeProject(path: string, deleteFiles: boolean = false) {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/roots?path=${encodeURIComponent(path)}&delete_files=${deleteFiles}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to remove project')
      return true
    } catch (e) {
      console.error(e)
      return false
    }
  }

  // Smart Discovery
  const discoveryRoot = ref('')

  async function fetchConfig() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/config')
        if (response.ok) {
            const data = await response.json()
            if (data.discovery_root) {
                discoveryRoot.value = data.discovery_root
            }
        }
    } catch (e) {
        console.error('Failed to fetch config', e)
    }
  }

  function setDiscoveryRoot(path: string) {
    discoveryRoot.value = path
    // No need to save to localStorage, backend handles it via /api/discover or we could add a specific config endpoint in future.
    // For now, /api/discover already updates it in backend.
  }

  async function discoverProjects(path: string) {
    try {
      // Optimistic update
      setDiscoveryRoot(path)
      
      const response = await fetch('http://127.0.0.1:8000/api/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      if (!response.ok) throw new Error('Discovery failed')
      const data = await response.json()
      return data.projects || []
    } catch (e) {
      console.error(e)
      return []
    }
  }

  async function createProject(parentPath: string, name: string, file: File | null) {
    try {
      const formData = new FormData()
      formData.append('parent_path', parentPath)
      formData.append('name', name)
      if (file) {
        formData.append('file', file)
      }

      const response = await fetch('http://127.0.0.1:8000/api/projects/create', {
        method: 'POST',
        body: formData, 
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to create project')
      }
      return true
    } catch (e) {
      console.error(e)
      throw e 
    }
  }

  async function uploadProjectFile(projectPath: string, file: File) {
    try {
        const formData = new FormData()
        formData.append('project_path', projectPath)
        formData.append('file', file)

        const response = await fetch('http://127.0.0.1:8000/api/projects/upload', {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const err = await response.json()
            throw new Error(err.detail || 'Failed to upload file')
        }
        return true
    } catch (e) {
        console.error(e)
        throw e
    }
  }

  async function runCommand(path: string, cmd: 'open' | 'dev') {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/projects/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, cmd })
      })
      if (!response.ok) throw new Error('Command failed')
      return true
    } catch (e: any) {
      console.error(e)
      throw e
    }
  }

  async function fetchReadme(path: string) {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/projects/readme?path=${encodeURIComponent(path)}`)
      if (!response.ok) throw new Error('Failed to fetch README')
      const data = await response.json()
      return data.content
    } catch (e) {
      console.error(e)
      throw e
    }
  }

  return { 
    projects, 
    isConnected, 
    connect, 
    addProject, 
    removeProject, 
    discoveryRoot, 
    setDiscoveryRoot, 
    discoverProjects, 
    fetchConfig, 
    createProject, 
    uploadProjectFile,
    runCommand,
    fetchReadme
  }
})
