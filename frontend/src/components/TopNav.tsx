import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Calendar, Cpu, Database } from 'lucide-react';

export const TopNav: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/patients?search=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-xs sticky top-0 z-10">
      {/* Search Input */}
      <div className="w-80 max-w-xs md:max-w-md">
        <form onSubmit={handleSearchSubmit} className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search patient ID, condition, or encounter..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs md:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 transition-all"
          />
        </form>
      </div>

      {/* Operational Badges & User Context */}
      <div className="flex items-center space-x-3">
        {/* Reporting Period */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 bg-slate-100 text-slate-700 rounded-md text-xs font-medium border border-slate-200/80">
          <Calendar className="w-3.5 h-3.5 text-slate-500" />
          <span>Week 42, 2026</span>
        </div>

        {/* Dataset Status */}
        <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-medium border border-blue-200/80">
          <Database className="w-3.5 h-3.5 text-blue-500" />
          <span>25k Synthetic Records</span>
        </div>

        {/* Model Version */}
        <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 bg-teal-50 text-teal-800 rounded-md text-xs font-medium border border-teal-200">
          <Cpu className="w-3.5 h-3.5 text-teal-600" />
          <span>v1.2.0 Calibrated HistGB</span>
        </div>

        {/* Clinical User Profile */}
        <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-teal-400 flex items-center justify-center font-bold text-xs shadow-xs">
            RN
          </div>
          <div className="hidden xl:block text-left">
            <span className="text-xs font-semibold text-slate-900 block leading-tight">Sarah Jenkins, RN</span>
            <span className="text-[11px] text-slate-500 block leading-tight">Transition Coordinator</span>
          </div>
        </div>
      </div>
    </header>
  );
};
