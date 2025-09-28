import { useMessages } from '../../hooks/useMessages';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Loading } from '../common/Loading';
import { ErrorMessage } from '../common/ErrorMessage';
import { AlertTriangle, Users } from 'lucide-react';

interface ChatInterfaceProps {
  sessionId: string | null;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const { messages, isLoading, error, postMessage, isEscalated } = useMessages(sessionId);

  if (isLoading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-800 to-gray-850 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-primary-950/5 to-primary-900/10 pointer-events-none"></div>
      
      {/* Chat content */}
      <div className="relative flex-1 flex flex-col">
        <MessageList messages={messages} />
        
        {/* Escalation banner */}
        {isEscalated && (
          <div className="flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-warning-900/80 to-warning-800/80 border-t border-warning-700/50 backdrop-blur-sm">
            <div className="flex items-center justify-center w-6 h-6 bg-warning-600 rounded-full">
              <Users size={14} className="text-warning-100" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-warning-100">
                Escalated to Human Agent
              </p>
              <p className="text-xs text-warning-200/80">
                A human specialist is now handling this conversation. You can continue chatting here.
              </p>
            </div>
            <AlertTriangle size={18} className="text-warning-400" />
          </div>
        )}
        
        <MessageInput onSendMessage={postMessage} />
      </div>
    </div>
  );
}
