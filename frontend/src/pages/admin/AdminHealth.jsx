import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, Database, Server, Smartphone, HardDrive, ShieldCheck, AlertTriangle } from 'lucide-react';
import apiClient from '../../api/client';

const AdminHealth = () => {
    const { data: health, isLoading } = useQuery({
        queryKey: ['adminHealth'],
        queryFn: async () => {
            const res = await apiClient.get('/admin/health');
            return res.data;
        },
        refetchInterval: 60000, // 1 minute
    });

    if (isLoading) return <div className="p-8 text-center text-gray-500">Monitoring system health...</div>;

    const components = [
        { name: 'API Server', status: health?.api, icon: <Activity className="w-6 h-6" />, desc: 'Node.js/FastAPI Application' },
        { name: 'Database', status: health?.db, icon: <Database className="w-6 h-6" />, desc: 'PostgreSQL DB' },
        { name: 'Cache & Queue', status: health?.redis, icon: <Server className="w-6 h-6" />, desc: 'Redis Instance' },
        { name: 'Storage', status: health?.minio, icon: <HardDrive className="w-6 h-6" />, desc: 'Minio S3 Storage' },
        { name: 'Antivirus', status: health?.clamav, icon: <ShieldCheck className="w-6 h-6" />, desc: 'ClamAV Scanner' },
    ];

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-2xl font-bold text-gray-900">System Health</h2>
                <p className="text-gray-600">Infrastructure and hardware monitoring.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {components.map((comp, i) => (
                    <div key={i} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-gray-50 rounded-lg text-gray-600">
                                {comp.icon}
                            </div>
                            <StatusIndicator status={comp.status} />
                        </div>
                        <h3 className="font-bold text-gray-900 mb-1">{comp.name}</h3>
                        <p className="text-xs text-gray-500">{comp.desc}</p>
                        {comp.status !== 'ok' && (
                            <div className="mt-4 p-2 bg-red-50 text-red-700 text-[10px] rounded font-mono break-words">
                                {String(comp.status)}
                            </div>
                        )}
                    </div>
                ))}

                {/* Worker Queue Card */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 ring-2 ring-primary-500 ring-offset-2">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-3 bg-primary-50 rounded-lg text-primary-600 font-bold uppercase text-xs">
                            Worker Queue
                        </div>
                        <Smartphone className="w-6 h-6 text-primary-300" />
                    </div>
                    <div className="text-4xl font-black text-gray-900 mb-1">
                        {health?.worker_queue_depth || 0}
                    </div>
                    <p className="text-xs text-gray-500 font-medium">Pending background tasks</p>
                    <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-primary-500 transition-all duration-1000"
                            style={{ width: `${Math.min((health?.worker_queue_depth || 0) * 10, 100)}%` }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatusIndicator = ({ status }) => {
    const isOk = status === 'ok';
    return (
        <div className={`flex items-center px-2 py-1 rounded-md text-[10px] font-black uppercase
      ${isOk ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}
        >
            {isOk ? 'Operational' : 'Critical'}
        </div>
    );
};

export default AdminHealth;
