import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { AuthProvider } from './hooks/useAuth';
import { SessionsProvider } from './hooks/useSessions';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <SessionsProvider>
        <App />
      </SessionsProvider>
    </AuthProvider>
  </React.StrictMode>
);
