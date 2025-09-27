import { Plus } from 'lucide-react';

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
      className="w-full inline-flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
    >
      <Plus size={16} />
      {isLoading ? 'Creating…' : 'New Session'}
    </button>
  );
}

