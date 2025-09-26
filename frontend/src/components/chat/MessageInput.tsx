import { useState } from 'react';
import { Send } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => Promise<void>;
}

export function MessageInput({ onSendMessage }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isSending) {
      setIsSending(true);
      await onSendMessage(input);
      setInput('');
      setIsSending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-gray-900 border-t border-gray-700">
      <div className="relative">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Type your message..."
          className="w-full bg-gray-700 text-white rounded-lg p-2 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          rows={2}
          disabled={isSending}
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-indigo-400 disabled:opacity-50"
        >
          <Send size={20} />
        </button>
      </div>
    </form>
  );
}

