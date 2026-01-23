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
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const isConnected = ref(false)
  let socket: WebSocket | null = null
  let retryTimer: number | null = null

  function connect() {
    if (socket) return

    // Assuming backend is on localhost:8000 based on main.py
    socket = new WebSocket('ws://localhost:8000/ws')

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

  return { projects, isConnected, connect }
})
