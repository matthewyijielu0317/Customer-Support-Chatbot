import { useMessages } from '../../hooks/useMessages';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Loading } from '../common/Loading';
import { ErrorMessage } from '../common/ErrorMessage';

interface ChatInterfaceProps {
  sessionId: string | null;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const { messages, isLoading, error, postMessage, isEscalated } = useMessages(sessionId);

  if (isLoading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="flex flex-col h-full bg-gray-800">
      <MessageList messages={messages} />
      {isEscalated && (
        <div className="px-4 py-2 bg-yellow-900 text-yellow-200 text-sm border-t border-yellow-700">
          A human specialist is handling this conversation. Feel free to continue typing here.
        </div>
      )}
      <MessageInput onSendMessage={postMessage} />
    </div>
  );
}
