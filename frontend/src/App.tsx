import { useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { AgentDashboardPage } from './pages/AgentDashboardPage';
import { Loading } from './components/common/Loading';

function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen bg-gradient-to-br from-gray-900 via-gray-925 to-gray-950 text-white flex items-center justify-center">
        <Loading message="Initializing application..." size="lg" />
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
