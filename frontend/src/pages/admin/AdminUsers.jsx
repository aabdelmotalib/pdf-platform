import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, UserX, UserCheck, Shield, Mail, Phone, Calendar, CreditCard } from 'lucide-react';
import apiClient from '../../api/client';

const AdminUsers = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const queryClient = useQueryClient();

    const { data: users, isLoading } = useQuery({
        queryKey: ['adminUsers', debouncedSearch],
        queryFn: async () => {
            const res = await apiClient.get(`/admin/users?search=${debouncedSearch}`);
            return res.data;
        }
    });

    const toggleStatusMutation = useMutation({
        mutationFn: async ({ userId, isActive }) => {
            await apiClient.patch(`/admin/users/${userId}`, { is_active: isActive });
        },
        onSuccess: () => {
            queryClient.invalidateQueries(['adminUsers']);
        }
    });

    // Handle search with debounce
    React.useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedSearch(searchTerm);
        }, 500);
        return () => clearTimeout(handler);
    }, [searchTerm]);

    if (isLoading && !users) return <div className="p-8 text-center text-gray-500">Loading users...</div>;

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
                    <p className="text-gray-600">View information and manage account permissions.</p>
                </div>

                <div className="relative w-full sm:w-64">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
                        <Search className="w-4 h-4" />
                    </span>
                    <input
                        type="text"
                        placeholder="Search by email..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="block w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                </div>
            </div>

            {/* Users Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">User Info</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Contact</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Current Plan</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Joined</th>
                                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                            {users?.map((user) => (
                                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="h-10 w-10 rounded-full bg-primary-50 flex items-center justify-center text-primary-600 font-bold">
                                                {user.email[0].toUpperCase()}
                                            </div>
                                            <div className="ml-4">
                                                <div className="text-sm font-semibold text-gray-900 flex items-center">
                                                    {user.email}
                                                    {user.role === 'admin' && <Shield className="w-3 h-3 text-primary-600 ml-1.5" title="Admin" />}
                                                </div>
                                                <div className="text-xs text-gray-400">ID: {user.id.substring(0, 8)}...</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-600 flex items-center"><Mail className="w-3 h-3 mr-1" /> {user.email}</div>
                                        <div className="text-sm text-gray-600 flex items-center"><Phone className="w-3 h-3 mr-1" /> {user.phone_number || "N/A"}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold inline-flex items-center uppercase
                      ${user.active_plan === 'monthly' ? 'bg-purple-100 text-purple-700' :
                                                user.active_plan === 'hourly' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}>
                                            <CreditCard className="w-3 h-3 mr-1" />
                                            {user.active_plan}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex flex-col gap-1">
                                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase w-fit
                        ${user.is_verified ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                                {user.is_verified ? 'Verified' : 'Pending'}
                                            </span>
                                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase w-fit
                        ${user.is_active ? 'bg-primary-100 text-primary-700' : 'bg-red-100 text-red-700'}`}>
                                                {user.is_active ? 'Active' : 'Banned'}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        <div className="flex items-center"><Calendar className="w-3 h-3 mr-1" /> {new Date(user.created_at).toLocaleDateString()}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right">
                                        <button
                                            onClick={() => toggleStatusMutation.mutate({ userId: user.id, isActive: !user.is_active })}
                                            className={`p-2 rounded-lg transition-colors
                        ${user.is_active
                                                    ? 'text-red-600 hover:bg-red-50'
                                                    : 'text-green-600 hover:bg-green-50'}`}
                                            title={user.is_active ? "Ban User" : "Unban User"}
                                        >
                                            {user.is_active ? <UserX className="w-5 h-5" /> : <UserCheck className="w-5 h-5" />}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {users?.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center text-gray-400 font-medium">
                                        No users found matching "{searchTerm}"
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

export default AdminUsers;
