import type { Message } from '../../services/types';
import { useRef, useEffect } from 'react';
import { Bot, User, Clock } from 'lucide-react';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatMessageTime = (timestamp?: string) => {
    if (!timestamp) return '';
    try {
      return new Date(timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return '';
    }
  };

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-600 hover:scrollbar-thumb-gray-500">
      <div className="p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <div className="w-16 h-16 bg-gray-700/50 rounded-full flex items-center justify-center mb-4">
              <Bot size={24} className="text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-300 mb-2">Start a conversation</h3>
            <p className="text-gray-500 max-w-md">
              Send a message to begin chatting with our intelligent support assistant.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex animate-slide-up ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div className={`flex items-start space-x-3 max-w-4xl ${
                msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  msg.role === 'user' 
                    ? 'bg-gradient-to-br from-primary-500 to-primary-600 shadow-soft' 
                    : 'bg-gradient-to-br from-gray-600 to-gray-700 shadow-soft'
                }`}>
                  {msg.role === 'user' ? (
                    <User size={16} className="text-white" />
                  ) : (
                    <Bot size={16} className="text-white" />
                  )}
                </div>

                {/* Message bubble */}
                <div className={`flex flex-col space-y-1 ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}>
                  {/* Message content */}
                  <div
                    className={`relative px-4 py-3 rounded-2xl shadow-soft transition-all duration-200 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white'
                        : 'bg-gradient-to-br from-gray-700 to-gray-750 text-gray-100 border border-gray-600/30'
                    }`}
                  >
                    {/* Message tail */}
                    <div className={`absolute top-3 w-3 h-3 rotate-45 ${
                      msg.role === 'user' 
                        ? 'bg-primary-600 -right-1.5' 
                        : 'bg-gray-700 -left-1.5'
                    }`}></div>

                    <p className="text-sm leading-relaxed whitespace-pre-wrap relative z-10">
                      {msg.content}
                    </p>
                  </div>

                  {/* Timestamp */}
                  {msg.timestamp && (
                    <div className={`flex items-center space-x-1 px-2 ${
                      msg.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}>
                      <Clock size={12} className="text-gray-500" />
                      <span className="text-xs text-gray-500">
                        {formatMessageTime(msg.timestamp)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        
        {/* Scroll anchor */}
        <div ref={endOfMessagesRef} className="h-4" />
      </div>
    </div>
  );
}
