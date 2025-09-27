import { Layout } from '../components/layout/Layout';
import { useSessions } from '../hooks/useSessions';
import { ChatInterface } from '../components/chat/ChatInterface';

export function WorkspacePage() {
  const { activeSessionId } = useSessions();

  return (
    <Layout>
      {activeSessionId ? (
        <ChatInterface sessionId={activeSessionId} />
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <p className="text-xl text-gray-300 max-w-2xl">
            Select a session or create a new one to start chatting
          </p>
        </div>
      )}
    </Layout>
  );
}
