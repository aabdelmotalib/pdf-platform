import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, CreditCard, FileText, CheckCircle, AlertCircle, Clock, TrendingUp } from 'lucide-react';
import apiClient from '../../api/client';

const AdminOverview = () => {
    const { data: stats, isLoading } = useQuery({
        queryKey: ['adminStats'],
        queryFn: async () => {
            const res = await apiClient.get('/admin/stats');
            return res.data;
        },
        refetchInterval: 30000, // 30 seconds
    });

    if (isLoading) return <div className="p-8 text-center text-gray-500">Loading statistics...</div>;

    const kpis = [
        { title: 'Total Users', value: stats?.total_users, icon: <Users className="w-6 h-6" />, color: 'bg-blue-500' },
        { title: 'Active Subs', value: stats?.active_subscriptions, icon: <TrendingUp className="w-6 h-6" />, color: 'bg-green-500' },
        { title: 'Revenue (Today)', value: `${stats?.revenue_today} EGP`, icon: <CreditCard className="w-6 h-6" />, color: 'bg-purple-500' },
        { title: 'Revenue (Month)', value: `${stats?.revenue_month} EGP`, icon: <CreditCard className="w-6 h-6" />, color: 'bg-indigo-500' },
    ];

    const jobStats = [
        { label: 'Queued', value: stats?.jobs_queued, icon: <Clock className="w-4 h-4" />, textColor: 'text-gray-600' },
        { label: 'Processing', value: stats?.jobs_processing, icon: <ActivityIcon className="w-4 h-4" />, textColor: 'text-blue-600' },
        { label: 'Completed (Today)', value: stats?.jobs_completed_today, icon: <CheckCircle className="w-4 h-4" />, textColor: 'text-green-600' },
        { label: 'Failed (Today)', value: stats?.jobs_failed_today, icon: <AlertCircle className="w-4 h-4" />, textColor: 'text-red-600' },
    ];

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
                <p className="text-gray-600">Real-time system performance and revenue tracking.</p>
            </div>

            {/* KPI Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {kpis.map((kpi, i) => (
                    <div key={i} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <div className={`${kpi.color} p-3 rounded-lg text-white`}>
                                {kpi.icon}
                            </div>
                        </div>
                        <div className="text-2xl font-bold text-gray-900">{kpi.value}</div>
                        <div className="text-sm text-gray-500 font-medium">{kpi.title}</div>
                    </div>
                ))}
            </div>

            {/* Job Activity */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
                <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center">
                    <FileText className="w-5 h-5 mr-2 text-primary-600" />
                    Conversion Engine Status
                </h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
                    {jobStats.map((stat, i) => (
                        <div key={i} className="flex flex-col">
                            <div className={`flex items-center text-sm font-semibold ${stat.textColor} mb-2`}>
                                {stat.icon}
                                <span className="ml-2">{stat.label}</span>
                            </div>
                            <div className="text-3xl font-bold text-gray-900">{stat.value}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const ActivityIcon = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
);

export default AdminOverview;
