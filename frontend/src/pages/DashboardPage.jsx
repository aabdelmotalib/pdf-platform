import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Upload, FileText, CheckCircle, Clock, AlertCircle, Download, LogOut, CreditCard } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import apiClient from '../api/client';
import useAuthStore from '../store/authStore';
import useSessionStore from '../store/sessionStore';
import SessionTimer from '../components/SessionTimer';

const DashboardPage = () => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [recentJobs, setRecentJobs] = useState([]);

    const navigate = useNavigate();
    const { user, logout } = useAuthStore();
    const { updateSession, planName } = useSessionStore();

    // Poll session status
    const { data: sessionData } = useQuery({
        queryKey: ['sessionStatus'],
        queryFn: async () => {
            const res = await apiClient.get('/session/status');
            updateSession(res.data);
            return res.data;
        },
        refetchInterval: 10000,
    });

    // Dropzone setup
    const onDrop = (acceptedFiles) => {
        setSelectedFile(acceptedFiles[0]);
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/msword': ['.doc'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
        },
        multiple: false,
    });

    const uploadMutation = useMutation({
        mutationFn: async (file) => {
            const formData = new FormData();
            formData.append('files', file);
            const res = await apiClient.post('/upload/files', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            return res.data;
        },
        onSuccess: (data) => {
            setRecentJobs((prev) => [
                { id: data.job_id, status: 'queued', filename: selectedFile.name, progress: 0 },
                ...prev.slice(0, 4),
            ]);
            setSelectedFile(null);
        },
    });

    const handleUpload = () => {
        if (selectedFile) {
            uploadMutation.mutate(selectedFile);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            {/* Header */}
            <nav className="bg-white shadow-sm px-4 py-3 flex justify-between items-center">
                <h1 className="text-xl font-bold text-primary-600">PDF Platform</h1>
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => navigate('/pricing')}
                        className="text-sm font-medium text-gray-600 hover:text-primary-600 flex items-center"
                    >
                        <CreditCard className="w-4 h-4 mr-1" />
                        Pricing
                    </button>
                    <div className="text-sm text-gray-600">
                        Hi, <span className="font-semibold">{user?.email?.split('@')[0]}</span>
                    </div>
                    <button
                        onClick={() => { logout(); navigate('/login'); }}
                        className="p-2 text-gray-400 hover:text-red-500"
                    >
                        <LogOut className="w-5 h-5" />
                    </button>
                </div>
            </nav>

            <main className="max-w-4xl mx-auto py-8 px-6">
                {/* Upload Section */}
                <div className="bg-white rounded-xl shadow-md p-8 mb-8">
                    <h2 className="text-lg font-semibold mb-6 flex items-center">
                        <Upload className="w-5 h-5 mr-2 text-primary-600" />
                        Upload File for Conversion
                    </h2>

                    <div
                        {...getRootProps()}
                        className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors
              ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'}`}
                    >
                        <input {...getInputProps()} />
                        <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                        <p className="text-gray-600">
                            {selectedFile ? selectedFile.name : "Drag & drop a file here, or click to select"}
                        </p>
                        <p className="text-xs text-gray-400 mt-2">
                            PDF, Word, Excel, Images (Max 100MB)
                        </p>
                    </div>

                    {selectedFile && (
                        <div className="mt-6 flex justify-end">
                            <button
                                onClick={handleUpload}
                                disabled={uploadMutation.isPending}
                                className="px-6 py-2 bg-primary-600 text-white rounded-md font-medium hover:bg-primary-700 focus:ring-4 focus:ring-primary-200 transition-all disabled:opacity-50"
                            >
                                {uploadMutation.isPending ? 'Uploading...' : 'Convert Now'}
                            </button>
                        </div>
                    )}

                    {uploadMutation.isError && (
                        <div className="mt-4 p-3 bg-red-50 text-red-600 rounded-md text-sm flex items-start">
                            <AlertCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                            {uploadMutation.error?.response?.data?.detail || 'Upload failed'}
                        </div>
                    )}
                </div>

                {/* Recent Jobs */}
                <div className="bg-white rounded-xl shadow-md overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                        <h3 className="font-semibold text-gray-800">Recent Conversions</h3>
                    </div>
                    <div className="divide-y divide-gray-100">
                        {recentJobs.length === 0 ? (
                            <div className="px-6 py-10 text-center text-gray-400">
                                No recent jobs. Start by uploading a file.
                            </div>
                        ) : (
                            recentJobs.map((job) => (
                                <JobRow key={job.id} job={job} />
                            ))
                        )}
                    </div>
                </div>
            </main>

            <SessionTimer />
        </div>
    );
};

// Internal component for Job Row to handle its own polling
const JobRow = ({ job }) => {
    const [status, setStatus] = useState(job.status);
    const [progress, setProgress] = useState(job.progress || 0);
    const [downloadUrl, setDownloadUrl] = useState(null);

    const { data } = useQuery({
        queryKey: ['jobStatus', job.id],
        queryFn: async () => {
            const res = await apiClient.get(`/upload/jobs/${job.id}/status`);
            return res.data;
        },
        enabled: status !== 'completed' && status !== 'failed',
        refetchInterval: (query) => {
            const currentStatus = query.state.data?.status;
            return (currentStatus === 'completed' || currentStatus === 'failed') ? false : 2000;
        },
    });

    useEffect(() => {
        if (data) {
            setStatus(data.status);
            setProgress(data.progress);
            if (data.download_url) setDownloadUrl(data.download_url);
        }
    }, [data]);

    const getStatusBadge = () => {
        switch (status) {
            case 'completed':
                return <span className="bg-green-100 text-green-700 px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center"><CheckCircle className="w-3 h-3 mr-1" /> Completed</span>;
            case 'processing':
                return <span className="bg-blue-100 text-blue-700 px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center animate-pulse"><Clock className="w-3 h-3 mr-1" /> Processing {progress}%</span>;
            case 'failed':
                return <span className="bg-red-100 text-red-700 px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center"><AlertCircle className="w-3 h-3 mr-1" /> Failed</span>;
            default:
                return <span className="bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center"><Clock className="w-3 h-3 mr-1" /> Queued</span>;
        }
    };

    return (
        <div className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
            <div className="flex items-center">
                <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center text-primary-600 mr-4">
                    <FileText className="w-6 h-6" />
                </div>
                <div>
                    <div className="text-sm font-medium text-gray-900 truncate max-w-[200px]">{job.filename}</div>
                    <div className="text-xs text-gray-500 mt-1">{getStatusBadge()}</div>
                </div>
            </div>

            {status === 'completed' && downloadUrl && (
                <a
                    href={downloadUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 text-primary-600 hover:bg-primary-50 rounded-full transition-colors"
                    title="Download Result"
                >
                    <Download className="w-5 h-5" />
                </a>
            )}
        </div>
    );
};

export default DashboardPage;
