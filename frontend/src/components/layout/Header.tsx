import { useAuth } from '../../hooks/useAuth';
import { LogOut } from 'lucide-react';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-800">
      <div className="text-lg font-semibold tracking-tight">Customer Support</div>
      <div className="flex items-center space-x-4">
        <span>{user?.email}</span>
        <button
          onClick={logout}
          className="flex items-center space-x-2 hover:text-indigo-400"
        >
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
}

