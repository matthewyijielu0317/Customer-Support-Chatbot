import { AlertTriangle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="flex flex-col justify-center items-center h-full text-red-500">
      <AlertTriangle size={48} />
      <p className="mt-4 text-lg">{message}</p>
    </div>
  );
}

