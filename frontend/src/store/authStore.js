import { create } from 'zustand';

const useAuthStore = create((set) => ({
    user: null,
    accessToken: null,
    isAuthenticated: false,

    login: (token, user) => set({
        accessToken: token,
        user: user,
        isAuthenticated: true
    }),

    logout: () => set({
        accessToken: null,
        user: null,
        isAuthenticated: false
    }),
}));

export default useAuthStore;
