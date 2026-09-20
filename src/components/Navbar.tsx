import React from 'react';
import { Activity } from 'lucide-react';

interface NavbarProps {
  onReset?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onReset }) => {
  return (
    <header className="border-b border-[#E2DFD7] bg-[#F7F5F0] sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Architectural Title */}
        <div 
          onClick={onReset}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-9 h-9 bg-[#0F172A] flex items-center justify-center text-white font-mono font-bold text-sm tracking-wider group-hover:bg-[#1D4ED8] transition-colors">
            MD
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-xs uppercase tracking-widest text-[#64748B] font-semibold">
                PS: T02 // Binary Beacons
              </span>
            </div>
            <h1 className="text-base font-extrabold tracking-tight text-[#0F172A] uppercase flex items-center gap-1.5">
              MargDarshak
              <span className="text-[11px] font-mono font-medium px-1.5 py-0.5 bg-[#E2DFD7] text-[#475569] rounded-none">
                v0.4.0
              </span>
            </h1>
          </div>
        </div>

        {/* Technical Status Badges */}
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-[#475569] border border-[#E2DFD7] bg-white px-3 py-1.5">
            <span className="w-2 h-2 rounded-full bg-[#15803D] animate-pulse"></span>
            <span>POSTGIS + REDIS // RAPTOR ONLINE</span>
          </div>

          <div className="flex items-center space-x-2 text-xs font-mono border border-[#0F172A] px-3 py-1.5 bg-[#0F172A] text-white">
            <Activity className="w-3.5 h-3.5 text-[#38BDF8]" />
            <span>P85 GUARANTEE</span>
          </div>
        </div>
      </div>
    </header>
  );
};
