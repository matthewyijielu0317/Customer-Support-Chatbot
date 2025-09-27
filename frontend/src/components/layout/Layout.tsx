import type { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <Header />
      <div className="grid flex-1 grid-cols-[1fr_3fr] overflow-hidden">
        <Sidebar />
        <main className="overflow-y-auto bg-gray-800 px-8 py-6">{children}</main>
      </div>
    </div>
  );
}
