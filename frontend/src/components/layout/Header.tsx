import { useAuth } from '../../hooks/useAuth';
import { LogOut, MessageCircle, Users } from 'lucide-react';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="relative flex items-center justify-between px-6 py-4 bg-gradient-to-r from-gray-900 via-gray-900 to-gray-850 border-b border-gray-800/50 backdrop-blur-sm">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-r from-primary-950/20 to-transparent opacity-50"></div>
      
      <div className="relative flex items-center space-x-3">
        <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg shadow-soft">
          <MessageCircle size={18} className="text-white" />
        </div>
        <div className="flex flex-col">
          <h1 className="text-lg font-semibold tracking-tight text-white">
            Customer Support
          </h1>
          <p className="text-xs text-gray-400">Intelligent Support Platform</p>
        </div>
      </div>

      <div className="relative flex items-center space-x-4">
        <div className="flex items-center space-x-3 px-3 py-2 bg-gray-800/50 rounded-xl border border-gray-700/50 backdrop-blur-sm">
          <div className="flex items-center justify-center w-6 h-6 bg-gradient-to-br from-gray-600 to-gray-700 rounded-full">
            <Users size={12} className="text-gray-300" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-200">{user?.email}</span>
            <span className="text-xs text-gray-400 capitalize">{user?.role}</span>
          </div>
        </div>
        
        <button
          onClick={logout}
          className="group flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-800/50 rounded-xl border border-transparent hover:border-gray-700/50 transition-all duration-200"
          title="Sign out"
        >
          <LogOut size={16} className="transition-transform group-hover:scale-110" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
}

