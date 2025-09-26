import { useMessages } from '../../hooks/useMessages';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Loading } from '../common/Loading';
import { ErrorMessage } from '../common/ErrorMessage';

interface ChatInterfaceProps {
  sessionId: string | null;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const { messages, isLoading, error, postMessage } = useMessages(sessionId);

  if (isLoading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="flex flex-col h-full bg-gray-800">
      <MessageList messages={messages} />
      <MessageInput onSendMessage={postMessage} />
    </div>
  );
}
