import { Loader2 } from 'lucide-react';

export function Loading() {
  return (
    <div className="flex justify-center items-center h-full">
      <Loader2 className="animate-spin text-indigo-500" size={48} />
    </div>
  );
}

