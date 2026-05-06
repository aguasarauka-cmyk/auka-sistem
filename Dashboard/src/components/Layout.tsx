import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, MapPinned, Users, Activity, MessageSquareDot, Settings } from 'lucide-react';
import { cn } from '../lib/utils';

export function Layout() {
  return (
    <div className="flex h-screen w-full bg-[#F1F5F2] text-[#2D3A3A] font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-[#1B4332] text-[#D8F3DC] flex flex-col p-6 hidden md:flex">
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 bg-[#95D5B2] rounded-full flex items-center justify-center shadow-sm">
            <div className="w-6 h-6 border-2 border-[#1B4332] rounded-full border-t-transparent animate-spin-slow"></div>
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight uppercase tracking-wider text-white">Arauka</h1>
            <p className="text-[10px] opacity-70 uppercase tracking-widest text-[#D8F3DC] m-0 leading-tight">Intelligence Hub</p>
          </div>
        </div>
        
        <nav className="flex-1 overflow-y-auto space-y-4">
          <NavItem to="/" icon={<LayoutDashboard size={20} />} label="Overview" />
          <NavItem to="/map" icon={<MapPinned size={20} />} label="Mapa Geográfico" />
          <NavItem to="/prospects" icon={<Users size={20} />} label="Prospectos" />
          <NavItem to="/agent-activity" icon={<Activity size={20} />} label="Actividad (Logs)" />
          <NavItem to="/chat" icon={<MessageSquareDot size={20} />} label="Auka Chat" />
        </nav>
        
        <div className="mt-auto p-4 bg-[#081C15] rounded-2xl">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[10px] uppercase font-bold text-[#74C69D]">Agent Status</span>
            <span className="flex h-2 w-2 rounded-full bg-[#52B788]"></span>
          </div>
          <p className="text-xs opacity-80 text-[#D8F3DC]">Scanning Caracas Metro Area...</p>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#F1F5F2]">
        <header className="h-16 flex-shrink-0 border-b border-[#D8E3DB] bg-[#F1F5F2] flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-serif font-bold text-[#1B4332] hidden sm:block">AUKA System</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-white rounded-full border border-[#D8E3DB] shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#52B788] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#52B788]"></span>
              </span>
              <span className="text-xs font-bold uppercase tracking-widest text-[#1B4332]">Online</span>
            </div>
          </div>
        </header>
        
        <main className="flex-1 overflow-auto relative p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => cn(
        "group cursor-pointer p-3 rounded-xl flex items-center gap-3 transition-colors border",
        isActive 
          ? "bg-[#2D6A4F] border-[#40916C] text-white" 
          : "border-transparent text-[#D8F3DC] hover:bg-[#2D6A4F] hover:border-[#40916C]/50"
      )}
    >
      {({ isActive }) => (
        <>
          <div className={cn("w-2 h-2 rounded-full flex-shrink-0", isActive ? "bg-[#B7E4C7]" : "bg-white opacity-20 group-hover:opacity-100 transition-opacity")}></div>
          <div className="flex items-center gap-2">
            <span className="opacity-70">{icon}</span>
            <span className="text-sm font-medium">{label}</span>
          </div>
        </>
      )}
    </NavLink>
  );
}
