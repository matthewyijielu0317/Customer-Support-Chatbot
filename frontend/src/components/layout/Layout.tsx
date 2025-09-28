import type { ReactNode } from 'react';
import { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Menu, X } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-900 via-gray-900 to-gray-925 text-white overflow-hidden">
      <Header />
      
      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Sidebar backdrop for mobile */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        
        {/* Sidebar */}
        <div className={`
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          fixed md:static inset-y-0 left-0 z-50 md:z-auto
          w-80 md:w-88 xl:w-96 flex-shrink-0
          transition-transform duration-300 ease-in-out
          h-full
        `}>
          <Sidebar />
        </div>
        
        {/* Mobile menu button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className={`md:hidden fixed top-20 z-50 flex items-center justify-center w-12 h-12 bg-gray-800/90 hover:bg-gray-700/90 border border-gray-700/50 rounded-xl shadow-medium backdrop-blur-sm transition-all duration-300 ${
            sidebarOpen ? 'left-[21rem]' : 'left-4'
          }`}
          aria-label="Toggle sidebar"
        >
          {sidebarOpen ? (
            <X size={20} className="text-gray-300" />
          ) : (
            <Menu size={20} className="text-gray-300" />
          )}
        </button>
        
        {/* Main content - slides with sidebar on mobile/tablet */}
        <main className={`
          flex-1 overflow-hidden bg-gradient-to-br from-gray-800 to-gray-850 relative
          transition-transform duration-300 ease-in-out md:transition-none
          ${sidebarOpen ? 'transform translate-x-80 md:translate-x-0' : 'transform translate-x-0'}
        `}>
          {/* Background decoration */}
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-primary-950/5 to-primary-900/10 pointer-events-none"></div>
          
          {/* Content container - full height for chat */}
          <div className="relative h-full">
            {children}
          </div>
          
          {/* Subtle border overlay */}
          <div className="absolute inset-0 border border-gray-700/30 pointer-events-none rounded-tl-2xl"></div>
        </main>
      </div>
    </div>
  );
}
