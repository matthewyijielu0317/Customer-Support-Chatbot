import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Paperclip } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => Promise<void>;
  disabled?: boolean;
}

export function MessageInput({ onSendMessage, disabled = false }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled) {
      return;
    }
    if (input.trim() && !isSending) {
      setIsSending(true);
      try {
        await onSendMessage(input.trim());
        setInput('');
      } finally {
        setIsSending(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isDisabled = isSending || disabled;
  const canSend = input.trim() && !isDisabled;

  return (
    <div className="border-t border-gray-700/50 bg-gradient-to-r from-gray-900 to-gray-850 backdrop-blur-sm">
      <form onSubmit={handleSubmit} className="p-4">
        <div className="relative">
          {/* Input container */}
          <div className="relative flex items-end space-x-3 bg-gray-800/50 rounded-2xl border border-gray-700/50 focus-within:border-primary-500/50 transition-colors duration-200 shadow-soft">
            {/* Attachment button */}
            <button
              type="button"
              className="flex-shrink-0 p-3 text-gray-400 hover:text-gray-300 transition-colors duration-200"
              disabled={isDisabled}
              title="Attach file (coming soon)"
            >
              <Paperclip size={18} />
            </button>

            {/* Text input */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isDisabled ? 'Please wait...' : 'Type your message... (Press Enter to send, Shift+Enter for new line)'}
              className="flex-1 bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none py-3 pr-4 text-sm leading-relaxed min-h-[24px] max-h-[120px]"
              rows={1}
              disabled={isDisabled}
            />

            {/* Send button */}
            <div className="flex-shrink-0 p-2">
              <button
                type="submit"
                disabled={!canSend}
                className={`group relative flex items-center justify-center w-8 h-8 rounded-xl transition-all duration-200 ${
                  canSend
                    ? 'bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-500 hover:to-primary-600 shadow-soft hover:shadow-medium text-white'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
                title={canSend ? 'Send message' : 'Type a message to send'}
              >
                {isSending ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Send size={16} className={`transition-transform ${canSend ? 'group-hover:scale-110' : ''}`} />
                )}
                
                {/* Hover effect */}
                {canSend && (
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary-400/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
                )}
              </button>
            </div>
          </div>

          {/* Character count and tips */}
          <div className="flex items-center justify-between mt-2 px-1">
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <span>Press Enter to send</span>
              <span>Shift+Enter for new line</span>
            </div>
            
            {input.length > 0 && (
              <div className="text-xs text-gray-500">
                {input.length} character{input.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
