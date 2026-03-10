import { create } from 'zustand';

const useSessionStore = create((set) => ({
    remainingSeconds: 0,
    filesUsed: 0,
    filesAllowed: 0,
    planName: 'free',
    isActive: false,

    updateSession: (data) => set({
        remainingSeconds: data.remaining_seconds,
        filesUsed: data.files_used,
        filesAllowed: data.files_allowed,
        planName: data.plan_name,
        isActive: data.is_active,
    }),
}));

export default useSessionStore;
