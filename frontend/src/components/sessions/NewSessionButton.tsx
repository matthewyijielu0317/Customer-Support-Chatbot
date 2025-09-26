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
      className="w-full flex items-center justify-center py-2 px-4 border border-dashed border-gray-600 rounded-md text-sm font-medium text-gray-300 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
    >
      <Plus size={16} className="mr-2" />
      {isLoading ? 'Creating...' : 'New Session'}
    </button>
  );
}

