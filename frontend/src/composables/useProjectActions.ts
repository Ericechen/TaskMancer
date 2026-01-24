import { ref } from 'vue'
import type { Project } from '../stores/projectStore'
import { useProjectStore } from '../stores/projectStore'
import Swal from 'sweetalert2'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

export function useProjectActions() {
    const projectStore = useProjectStore()
    const isUnlinking = ref(false)
    const isDeleting = ref(false)

    async function handleUnlink(project: Project) {
        const result = await Swal.fire({
            title: 'Remove Project?',
            html: `Are you sure you want to stop tracking <b>${project.name}</b>?<br><small class="opacity-50">This will only remove it from the dashboard.</small>`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, remove',
            cancelButtonText: 'Cancel'
        })

        if (result.isConfirmed) {
            isUnlinking.value = true
            try {
                await projectStore.removeProject(project.path, false)
                Swal.fire({
                    title: 'Removed!',
                    text: 'Project tracking removed.',
                    icon: 'success',
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000
                })
            } catch (e: any) {
                Swal.fire('Error', e.message, 'error')
            } finally {
                isUnlinking.value = false
            }
        }
    }

    async function handleDelete(project: Project) {
        const result = await Swal.fire({
            title: 'DELETE FOLDER?',
            html: `THIS IS IRREVERSIBLE!<br>Do you really want to delete <b>${project.name}</b> and all its files from disk?`,
            icon: 'error',
            showCancelButton: true,
            customClass: {
                confirmButton: 'bg-danger hover:bg-danger/80'
            },
            confirmButtonText: 'DELETE EVERYTHING',
            cancelButtonText: 'Cancel'
        })

        if (result.isConfirmed) {
            isDeleting.value = true
            try {
                await projectStore.removeProject(project.path, true)
                Swal.fire({
                    title: 'Deleted!',
                    text: 'Project folder has been deleted.',
                    icon: 'success',
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000
                })
            } catch (e: any) {
                Swal.fire('Error', e.message, 'error')
            } finally {
                isDeleting.value = false
            }
        }
    }

    async function handleAction(action: string, path: string) {
        try {
            await projectStore.executeAction(action, path)
        } catch (e: any) {
            Swal.fire('Action Failed', e.message, 'error')
        }
    }

    async function toggleDev(project: Project) {
        const isRunning = project.process?.is_running;
        if (isRunning) {
            const result = await Swal.fire({
                title: 'Stop Service?',
                html: `Are you sure you want to terminate <b class="text-accent">${project.name}</b>?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Yes, Stop',
                cancelButtonText: 'Cancel'
            })
            if (result.isConfirmed) {
                handleAction('stop', project.path)
            }
        } else {
            handleAction('start.bat', project.path)
        }
    }

    async function handleFileChange(event: Event, path: string) {
        const target = event.target as HTMLInputElement
        if (target.files && target.files.length > 0) {
            try {
                await projectStore.uploadFiles(path, target.files)
                Swal.fire({
                    title: 'Uploaded!',
                    text: 'Files uploaded successfully.',
                    icon: 'success',
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000
                })
            } catch (e: any) {
                Swal.fire('Upload Failed', e.message, 'error')
            }
        }
    }

    async function handleInfo(project: Project) {
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/projects/readme?path=${encodeURIComponent(project.path)}`)
            if (!response.ok) throw new Error('Failed to fetch README')
            const data = await response.json()

            const htmlContent = DOMPurify.sanitize(await marked(data.content))

            Swal.fire({
                html: `
                <div class="text-left">
                    <div class="flex items-center space-x-3 mb-8 border-b border-white/5 pb-6">
                        <div class="w-10 h-10 rounded-xl bg-accent/20 flex items-center justify-center text-accent">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                        </div>
                        <div>
                            <h2 class="text-xl font-display font-bold text-primary m-0">${project.name}</h2>
                            <p class="text-xs text-secondary/50 font-mono m-0 uppercase tracking-widest mt-0.5">Project Documentation</p>
                        </div>
                    </div>
                    <div class="tm-readme-content">${htmlContent}</div>
                </div>
            `,
                width: '850px',
                background: 'rgba(5, 5, 5, 0.95)',
                color: '#F8FAFC',
                backdrop: 'rgba(0,0,0,0.8)',
                showCloseButton: true,
                showConfirmButton: false,
                customClass: {
                    popup: 'rounded-3xl border border-white/10 shadow-2xl backdrop-blur-xl p-8',
                    htmlContainer: 'p-0 m-0 overflow-hidden'
                },
                showClass: {
                    popup: 'animate__animated animate__fadeInUp animate__faster'
                },
                hideClass: {
                    popup: 'animate__animated animate__fadeOutDown animate__faster'
                }
            })
        } catch (e: any) {
            Swal.fire({
                icon: 'error',
                title: 'Failed to load README',
                text: e.message || 'Error occurred while fetching documentation',
                background: '#0a0a0a',
                color: '#e5e7eb',
                customClass: {
                    popup: 'rounded-2xl border border-white/10'
                }
            })
        }
    }

    return {
        isUnlinking,
        isDeleting,
        handleUnlink,
        handleDelete,
        handleAction,
        toggleDev,
        handleFileChange,
        handleInfo
    }
}
