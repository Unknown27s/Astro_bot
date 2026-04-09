import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { X } from 'lucide-react';
import {
  Layout,
  FileText,
  Users,
  Zap,
  Settings,
  LogOut,
} from 'lucide-react';
import { cn } from '../../utils/cn';

const menuItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: Layout,
    href: '/admin/dashboard',
  },
  {
    id: 'documents',
    label: 'Documents',
    icon: FileText,
    href: '/admin/documents',
  },
  {
    id: 'users',
    label: 'Users',
    icon: Users,
    href: '/admin/users',
  },
  {
    id: 'rate-limiting',
    label: 'Rate Limiting',
    icon: Zap,
    href: '/admin/rate-limiting',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    href: '/admin/settings',
  },
];

export default function AdminSidebar({ isOpen, onClose }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('astrobot_user');
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
        />
      )}

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -280 }}
        animate={{ x: isOpen ? 0 : -280 }}
        transition={{ duration: 0.3 }}
        className={cn(
          'w-64 bg-white border-r border-slate-200 flex flex-col fixed md:relative z-50 md:z-auto h-screen md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        {/* Header */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-purple-600">AstroBot</h1>
            <button
              onClick={onClose}
              className="md:hidden p-1 hover:bg-slate-100 rounded transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-1">Admin Panel</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;

            return (
              <button
                key={item.id}
                onClick={() => {
                  navigate(item.href);
                  onClose?.();
                }}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                  isActive
                    ? 'bg-purple-600 text-white shadow-md'
                    : 'text-slate-600 hover:bg-slate-100'
                )}
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium text-sm">{item.label}</span>
                {isActive && (
                  <div className="ml-auto h-2 w-2 bg-white rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 space-y-2">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 transition-colors duration-200"
          >
            <LogOut className="h-5 w-5" />
            <span className="font-medium text-sm">Logout</span>
          </button>
        </div>
      </motion.aside>
    </>
  );
}
