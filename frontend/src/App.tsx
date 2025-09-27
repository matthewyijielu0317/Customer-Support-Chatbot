import { useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { AgentDashboardPage } from './pages/AgentDashboardPage';

function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen bg-gray-900 text-white flex items-center justify-center">
        <h1 className="text-4xl font-bold">Loading...</h1>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  if (user.role === 'agent') {
    return <AgentDashboardPage />;
  }

  return <WorkspacePage />;
}

export default App;
