import { Plus, Loader2 } from 'lucide-react';

interface NewSessionButtonProps {
  onClick: () => void;
  isLoading: boolean;
}

export function NewSessionButton({
  onClick,
  isLoading,
}: NewSessionButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="group relative inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-500 hover:to-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-950 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-soft hover:shadow-medium transition-all duration-200 overflow-hidden"
    >
      {/* Background animation */}
      <div className="absolute inset-0 bg-gradient-to-r from-primary-400/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
      
      {/* Button content */}
      <div className="relative flex items-center gap-2">
        {isLoading ? (
          <Loader2 size={16} className="animate-spin" />
        ) : (
          <Plus size={16} className="transition-transform group-hover:scale-110" />
        )}
        <span className="font-medium">
          {isLoading ? 'Creating…' : 'New Session'}
        </span>
      </div>
    </button>
  );
}

