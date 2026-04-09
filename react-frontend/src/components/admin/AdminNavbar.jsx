import { useEffect, useState } from 'react';
import { Menu, Search, Sun, Moon, User, ChevronDown } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { cn } from '../../utils/cn';

export default function AdminNavbar({ onMenuClick, sidebarOpen }) {
  const [user, setUser] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const { isDark, toggleTheme } = useTheme();

  useEffect(() => {
    const userStr = localStorage.getItem('astrobot_user');
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch {
        // Error parsing user
      }
    }
  }, []);

  return (
    <nav className="bg-white border-b border-slate-200 px-4 md:px-8 py-4 flex items-center justify-between">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        {/* Menu Toggle */}
        <button
          onClick={onMenuClick}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors md:hidden"
          title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          <Menu className="h-5 w-5 text-slate-600" />
        </button>

        {/* Search Bar */}
        <div className="hidden sm:flex items-center gap-2 bg-slate-100 px-4 py-2 rounded-lg flex-1 max-w-xs">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent border-none outline-none text-sm w-full text-slate-800 placeholder-slate-500"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-600 hover:text-slate-800"
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          {isDark ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </button>

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-3 px-3 py-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <div className="h-8 w-8 bg-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
              {user?.username?.[0]?.toUpperCase() || 'A'}
            </div>
            <div className="hidden sm:flex flex-col items-start">
              <span className="text-sm font-medium text-slate-800">
                {user?.full_name || user?.username || 'Admin'}
              </span>
              <span className="text-xs text-slate-500 capitalize">
                {user?.role || 'admin'}
              </span>
            </div>
            <ChevronDown
              className={cn(
                'h-4 w-4 text-slate-500 transition-transform',
                dropdownOpen && 'rotate-180'
              )}
            />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-10">
              <a
                href="#profile"
                className="block px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Profile Settings
              </a>
              <a
                href="#help"
                className="block px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Help & Support
              </a>
              <hr className="my-2" />
              <button
                onClick={() => {
                  localStorage.removeItem('astrobot_user');
                  localStorage.removeItem('token');
                  window.location.href = '/login';
                }}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
