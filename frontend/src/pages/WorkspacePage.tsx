import { Layout } from '../components/layout/Layout';
import { useSessions } from '../hooks/useSessions';
import { ChatInterface } from '../components/chat/ChatInterface';
import { MessageCircle, Plus, Sparkles } from 'lucide-react';

export function WorkspacePage() {
  const { activeSessionId, createNewSession } = useSessions();

  return (
    <Layout>
      {activeSessionId ? (
        <ChatInterface sessionId={activeSessionId} />
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-center p-8 overflow-y-auto">
          {/* Welcome section */}
          <div className="space-y-8 max-w-2xl animate-fade-in">
            {/* Main icon */}
            <div className="flex items-center justify-center w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-600 rounded-3xl shadow-large mx-auto">
              <MessageCircle size={40} className="text-white" />
            </div>
            
            {/* Welcome message */}
            <div className="space-y-4">
              <h1 className="text-3xl font-bold text-white">
                Welcome to Customer Support
              </h1>
              <p className="text-xl text-gray-300 leading-relaxed">
                Start a conversation with our intelligent support assistant to get help with your questions
              </p>
            </div>
            
            {/* Features grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
              <div className="text-center space-y-3">
                <div className="flex items-center justify-center w-12 h-12 bg-gray-800/50 rounded-xl mx-auto">
                  <Sparkles size={20} className="text-primary-400" />
                </div>
                <h3 className="font-semibold text-gray-200">AI-Powered</h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Get instant responses from our intelligent AI assistant
                </p>
              </div>
              
              <div className="text-center space-y-3">
                <div className="flex items-center justify-center w-12 h-12 bg-gray-800/50 rounded-xl mx-auto">
                  <MessageCircle size={20} className="text-primary-400" />
                </div>
                <h3 className="font-semibold text-gray-200">24/7 Available</h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Support is available around the clock whenever you need it
                </p>
              </div>
              
              <div className="text-center space-y-3">
                <div className="flex items-center justify-center w-12 h-12 bg-gray-800/50 rounded-xl mx-auto">
                  <Plus size={20} className="text-primary-400" />
                </div>
                <h3 className="font-semibold text-gray-200">Easy to Use</h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Simple interface designed for quick problem resolution
                </p>
              </div>
            </div>
            
            {/* CTA button */}
            <div className="pt-8">
              <button
                onClick={createNewSession}
                className="group inline-flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-500 hover:to-primary-600 text-white font-semibold rounded-2xl shadow-medium hover:shadow-large transition-all duration-200 transform hover:scale-105"
              >
                <Plus size={20} className="transition-transform group-hover:rotate-90" />
                <span>Start New Conversation</span>
              </button>
            </div>
            
            {/* Help text */}
            <p className="text-sm text-gray-500 mt-6">
              You can also create a new session from the sidebar or select an existing one to continue
            </p>
          </div>
        </div>
      )}
    </Layout>
  );
}
