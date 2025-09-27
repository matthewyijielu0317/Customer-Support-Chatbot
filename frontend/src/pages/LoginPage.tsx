import { useState } from 'react';
import { LoginForm } from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const { login } = useAuth();

  const handleLogin = async (data: { email: string; passcode: string }) => {
    setIsLoggingIn(true);
    try {
      await login(data.email, data.passcode);
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="h-screen w-full bg-gray-900 text-white flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-gray-800 border border-gray-700 rounded-xl shadow-lg p-8 text-center space-y-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Customer Support Chatbot</h2>
        </div>
        <div className="bg-gray-900/70 border border-gray-700 rounded-lg p-6 text-left">
          <h3 className="text-lg font-semibold text-center mb-4">Login Form</h3>
          <LoginForm onLogin={handleLogin} isLoggingIn={isLoggingIn} />
        </div>
        <p className="text-sm text-gray-400">Demo credentials available below</p>
      </div>
    </div>
  );
}
