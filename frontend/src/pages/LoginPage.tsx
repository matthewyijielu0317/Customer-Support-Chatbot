import { useState } from 'react';
import { LoginForm } from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';
import { MessageCircle, Shield, Zap, Users } from 'lucide-react';

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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-925 to-gray-950 text-white flex items-center justify-center px-4 py-8">
      {/* Background decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-primary-600/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-primary-500/5 to-transparent rounded-full blur-3xl"></div>
      </div>

      <div className="relative w-full max-w-md animate-fade-in">
        {/* Main login card */}
        <div className="bg-gradient-to-br from-gray-800/80 to-gray-850/80 border border-gray-700/50 rounded-3xl shadow-large backdrop-blur-sm p-8 space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl shadow-medium mx-auto">
              <MessageCircle size={28} className="text-white" />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Customer Support
              </h1>
              <p className="text-gray-400 text-sm">
                Intelligent Support Platform
              </p>
            </div>
          </div>

          {/* Features */}
          <div className="grid grid-cols-3 gap-4 py-4">
            <div className="text-center space-y-2">
              <div className="flex items-center justify-center w-10 h-10 bg-gray-700/50 rounded-xl mx-auto">
                <Zap size={16} className="text-primary-400" />
              </div>
              <p className="text-xs text-gray-400">Fast</p>
            </div>
            <div className="text-center space-y-2">
              <div className="flex items-center justify-center w-10 h-10 bg-gray-700/50 rounded-xl mx-auto">
                <Shield size={16} className="text-primary-400" />
              </div>
              <p className="text-xs text-gray-400">Secure</p>
            </div>
            <div className="text-center space-y-2">
              <div className="flex items-center justify-center w-10 h-10 bg-gray-700/50 rounded-xl mx-auto">
                <Users size={16} className="text-primary-400" />
              </div>
              <p className="text-xs text-gray-400">Smart</p>
            </div>
          </div>

          {/* Login form */}
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-gray-200 mb-2">Sign In</h2>
              <p className="text-sm text-gray-400">Enter your credentials to continue</p>
            </div>
            
            <LoginForm onLogin={handleLogin} isLoggingIn={isLoggingIn} />
          </div>

          {/* Demo credentials notice */}
          <div className="bg-gray-900/50 border border-gray-700/50 rounded-xl p-4 text-center">
            <p className="text-xs text-gray-400 mb-2">Demo credentials pre-filled</p>
            <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
              <div className="w-1 h-1 bg-success-500 rounded-full animate-pulse"></div>
              <span>Ready to test</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-xs text-gray-500">
            © 2024 Customer Support Platform. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
