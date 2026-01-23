import Swal from 'sweetalert2'

export const $swal = Swal.mixin({
    background: '#121212', // bg-surface
    color: '#F8FAFC',      // text-primary
    confirmButtonColor: '#8B5CF6', // bg-accent
    cancelButtonColor: '#262626', // bg-zinc-800
    customClass: {
        popup: 'border border-[#2A2A2A] rounded-2xl shadow-2xl p-6', // border-border
        title: 'font-display font-bold tracking-tight mb-2',
        htmlContainer: 'text-left leading-relaxed',
        confirmButton: 'font-bold px-8 py-3 rounded-xl text-sm transition-all hover:scale-105 active:scale-95',
        cancelButton: 'font-bold px-8 py-3 rounded-xl text-sm text-[#94A3B8] hover:text-white transition-colors', // text-secondary
    },
    buttonsStyling: false
})

export const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    background: '#121212',
    color: '#F8FAFC',
    customClass: {
        popup: 'border border-[#2A2A2A] rounded-lg shadow-xl'
    },
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
})
