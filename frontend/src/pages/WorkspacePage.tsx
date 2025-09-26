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
        <div className="flex flex-col items-center justify-center h-full">
          <h1 className="text-3xl font-bold">
            Select a session or create a new one to start chatting
          </h1>
        </div>
      )}
    </Layout>
  );
}
