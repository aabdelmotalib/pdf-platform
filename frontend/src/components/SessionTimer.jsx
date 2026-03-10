import React from 'react';
import useSessionStore from '../store/sessionStore';
import { Clock, AlertCircle } from 'lucide-react';

const SessionTimer = () => {
    const { remainingSeconds, filesUsed, filesAllowed, planName, isActive } = useSessionStore();

    if (planName !== 'hourly' || !isActive) return null;

    const formatTime = (seconds) => {
        if (seconds <= 0) return "00:00:00";
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const isLowTime = remainingSeconds < 300; // 5 minutes

    return (
        <>
            <div className={`fixed bottom-0 left-0 right-0 h-14 flex items-center justify-between px-6 shadow-2xl transition-colors duration-500 z-40
        ${isLowTime ? 'bg-red-600 text-white' : 'bg-primary-600 text-white'}`}
            >
                <div className="flex items-center font-medium text-sm sm:text-base">
                    <Clock className={`w-5 h-5 mr-3 ${isLowTime ? 'animate-pulse' : ''}`} />
                    <span>
                        Session: <span className="font-mono font-bold">{formatTime(remainingSeconds)}</span> remaining
                        {isLowTime && <span className="hidden sm:inline ml-2">— Session ending soon!</span>}
                    </span>
                </div>

                <div className="flex items-center text-sm sm:text-base bg-white/20 px-3 py-1 rounded-full font-semibold">
                    Files: {filesUsed}/{filesAllowed}
                </div>
            </div>

            {/* Modal for expired session */}
            {remainingSeconds <= 0 && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-6 z-50 animate-in fade-in duration-300">
                    <div className="bg-white rounded-2xl p-8 max-w-sm w-full text-center shadow-2xl">
                        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 text-red-600">
                            <AlertCircle className="w-10 h-10" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Session Ended</h3>
                        <p className="text-gray-600 mb-8">
                            Your hourly session has expired. To continue converting files, please purchase another hour.
                        </p>
                        <button
                            onClick={() => window.location.href = '/pricing'}
                            className="w-full py-3 bg-primary-600 text-white rounded-xl font-bold hover:bg-primary-700 shadow-lg shadow-primary-200 transition-all active:scale-[0.98]"
                        >
                            Extend Session
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default SessionTimer;
