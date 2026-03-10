import React from 'react';
import { Navigate, Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, FileText, Activity, LogOut, ArrowLeft } from 'lucide-react';
import useAuthStore from '../../store/authStore';

const AdminLayout = () => {
  const { user, logout, isAuthenticated } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();

  // Role check
  if (!isAuthenticated || user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  const menuItems = [
    { title: 'Overview', path: '/admin', icon: <LayoutDashboard className="w-5 h-5" /> },
    { title: 'Jobs', path: '/admin/jobs', icon: <FileText className="w-5 h-5" /> },
    { title: 'Users', path: '/admin/users', icon: <Users className="w-5 h-5" /> },
    { title: 'Health', path: '/admin/health', icon: <Activity className="w-5 h-5" /> },
  ];

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col hidden md:flex">
        <div className="p-6">
          <h1 className="text-xl font-bold text-primary-600 flex items-center">
            <Activity className="w-6 h-6 mr-2" />
            Admin Panel
          </h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-1">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors
                ${location.pathname === item.path 
                  ? 'bg-primary-50 text-primary-700' 
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.title}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <button 
            onClick={() => navigate('/dashboard')}
            className="w-full flex items-center px-4 py-3 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5 mr-3" />
            Exit Admin
          </button>
          <button 
            onClick={() => { logout(); navigate('/login'); }}
            className="w-full flex items-center px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg mt-1"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Mobile Header */}
        <header className="bg-white border-b border-gray-200 p-4 flex items-center justify-between md:hidden">
          <h1 className="text-lg font-bold text-primary-600">Admin Panel</h1>
          <button onClick={() => navigate('/dashboard')} className="p-2 text-gray-600">
            <ArrowLeft className="w-6 h-6" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;
