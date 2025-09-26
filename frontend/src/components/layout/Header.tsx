import { useAuth } from '../../hooks/useAuth';
import { LogOut } from 'lucide-react';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between p-4 bg-gray-900 border-b border-gray-700">
      <div className="text-xl font-bold">Customer Support</div>
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

