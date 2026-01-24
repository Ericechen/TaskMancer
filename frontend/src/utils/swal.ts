import Swal from 'sweetalert2'

export const $swal = Swal.mixin({
    background: 'radial-gradient(circle at top left, rgba(20, 20, 20, 0.9), rgba(5, 5, 5, 0.98))',
    color: '#F8FAFC',
    backdrop: `rgba(0, 0, 0, 0.45) backdrop-blur-md`,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#262626',
    customClass: {
        popup: 'border border-white/10 rounded-[2rem] shadow-[0_25px_80px_-15px_rgba(0,0,0,0.8)] backdrop-blur-3xl p-10 ring-1 ring-white/20',
        title: 'text-2xl font-display font-black tracking-tight text-white mb-4',
        htmlContainer: 'text-secondary font-medium text-sm leading-relaxed mb-8 px-2',
        actions: 'flex gap-4 w-full mt-2',
        confirmButton: 'flex-1 bg-gradient-to-r from-danger/90 to-danger font-bold px-8 py-4 rounded-2xl text-[10px] uppercase tracking-[0.2em] transition-all hover:translate-y-[-2px] hover:shadow-[0_8px_25px_-5px_rgba(239,68,68,0.5)] active:scale-95 text-white',
        cancelButton: 'flex-1 bg-white/[0.03] border border-white/10 font-bold px-8 py-4 rounded-2xl text-[10px] uppercase tracking-[0.2em] text-secondary hover:text-white hover:bg-white/[0.08] transition-all active:scale-95',
        icon: 'border-white/10 scale-90 mt-0'
    },
    buttonsStyling: false,
    showClass: {
        popup: 'animate__animated animate__fadeInDown animate__faster'
    },
    hideClass: {
        popup: 'animate__animated animate__fadeOutUp animate__faster'
    }
})

export const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 2500,
    timerProgressBar: true,
    background: 'rgba(10, 10, 10, 0.9)',
    color: '#F8FAFC',
    customClass: {
        popup: 'border border-white/10 rounded-2xl shadow-2xl backdrop-blur-xl'
    },
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
})
