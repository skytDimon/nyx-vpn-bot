import { Outlet } from 'react-router-dom';
import { BottomNav } from './BottomNav';

export function Layout() {
  return (
    <div className="min-h-screen bg-[#02007F] font-mono flex flex-col">
      {/* Main content area */}
      <main className="flex-1 px-3 pt-3 pb-[72px] overflow-y-auto">
        <Outlet />
      </main>

      {/* XP Taskbar */}
      <BottomNav />
    </div>
  );
}
