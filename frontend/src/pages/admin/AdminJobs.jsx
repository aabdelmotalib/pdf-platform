import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, RefreshCw, CheckCircle, Clock, AlertCircle, PlayCircle, MoreHorizontal } from 'lucide-react';
import apiClient from '../../api/client';

const AdminJobs = () => {
    const [statusFilter, setStatusFilter] = useState('all');
    const queryClient = useQueryClient();

    const { data: jobs, isLoading, refetch } = useQuery({
        queryKey: ['adminJobs', statusFilter],
        queryFn: async () => {
            const res = await apiClient.get(`/admin/jobs?status=${statusFilter}`);
            return res.data;
        },
        refetchInterval: 10000, // 10 seconds
    });

    const retryMutation = useMutation({
        mutationFn: async (jobId) => {
            await apiClient.post(`/admin/jobs/${jobId}/retry`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries(['adminJobs']);
            queryClient.invalidateQueries(['adminStats']);
        },
    });

    if (isLoading) return <div className="p-8 text-center text-gray-500">Loading jobs...</div>;

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Job Management</h2>
                    <p className="text-gray-600">Monitor and recover file conversion jobs.</p>
                </div>
                <button
                    onClick={() => refetch()}
                    className="flex items-center px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 shadow-sm transition-colors"
                >
                    <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 overflow-x-auto">
                {['all', 'queued', 'processing', 'completed', 'failed'].map((status) => (
                    <button
                        key={status}
                        onClick={() => setStatusFilter(status)}
                        className={`px-6 py-3 text-sm font-medium capitalize border-b-2 transition-colors whitespace-nowrap
              ${statusFilter === status
                                ? 'border-primary-600 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
                    >
                        {status}
                    </button>
                ))}
            </div>

            {/* Jobs Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Job ID</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">User</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Created At</th>
                                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                            {jobs?.map((job) => (
                                <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">
                                        {job.id.substring(0, 8)}...
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {job.user_email}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 capitalize">
                                        {job.job_type}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <StatusBadge status={job.status} error={job.error_message} />
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(job.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right">
                                        {job.status === 'failed' && (
                                            <button
                                                onClick={() => retryMutation.mutate(job.id)}
                                                disabled={retryMutation.isPending}
                                                className="p-1 px-3 text-xs font-bold bg-primary-50 text-primary-600 rounded-md hover:bg-primary-100 flex items-center inline-flex ml-auto transition-all"
                                            >
                                                <PlayCircle className="w-3 h-3 mr-1" />
                                                {retryMutation.isPending ? '...' : 'Retry'}
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {jobs?.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center text-gray-400">
                                        No jobs found for this filter.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const StatusBadge = ({ status, error }) => {
    const commonClasses = "px-2.5 py-1 rounded-full text-xs font-bold inline-flex items-center";

    switch (status) {
        case 'completed':
            return <span className={`${commonClasses} bg-green-100 text-green-700`}><CheckCircle className="w-3 h-3 mr-1" /> Completed</span>;
        case 'processing':
            return <span className={`${commonClasses} bg-blue-100 text-blue-700 animate-pulse`}><RefreshCw className="w-3 h-3 mr-1 animate-spin" /> Processing</span>;
        case 'failed':
            return (
                <span
                    className={`${commonClasses} bg-red-100 text-red-700 cursor-help group relative`}
                    title={error || "Unknown error"}
                >
                    <AlertCircle className="w-3 h-3 mr-1" /> Failed
                    {error && (
                        <div className="absolute bottom-full mb-2 hidden group-hover:block w-48 bg-gray-900 text-white text-[10px] p-2 rounded shadow-lg z-50">
                            {error}
                        </div>
                    )}
                </span>
            );
        default:
            return <span className={`${commonClasses} bg-gray-100 text-gray-500`}><Clock className="w-3 h-3 mr-1" /> {status}</span>;
    }
};

export default AdminJobs;
