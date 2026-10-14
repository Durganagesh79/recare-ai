import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Activity,
  PhoneCall,
  BarChart3,
  Scale,
  Sparkles,
  FileText,
  Database,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  HeartPulse,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const navItems = [
    { to: '/', label: 'Overview Dashboard', icon: LayoutDashboard },
    { to: '/patients', label: 'Patient Registry', icon: Users },
    { to: '/risk-prediction', label: 'Readmission Risk', icon: Activity },
    { to: '/call-list', label: 'Monday Morning Call List', icon: PhoneCall, badge: '50 Cap' },
    { to: '/evaluation', label: 'Model Evaluation', icon: BarChart3 },
    { to: '/fairness', label: 'Fairness & Bias Audit', icon: Scale },
    { to: '/intervention-planner', label: 'Intervention Planner', icon: Sparkles },
    { to: '/reports', label: 'Reports & Exports', icon: FileText },
    { to: '/datasets', label: 'Dataset & Data Quality', icon: Database },
    { to: '/settings', label: 'Settings & Model Info', icon: ShieldCheck },
  ];

  return (
    <aside
      className={`bg-slate-900 text-slate-300 border-r border-slate-800 transition-all duration-300 flex flex-col flex-shrink-0 z-20 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Platform Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
        {!collapsed && (
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <HeartPulse className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <span className="font-bold text-white text-base tracking-tight block">ReCare AI</span>
              <span className="text-[10px] text-teal-400/90 font-medium tracking-wide block uppercase">Care Intervention</span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-full flex justify-center">
            <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <HeartPulse className="w-5 h-5 text-teal-400" />
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                  isActive
                    ? 'bg-teal-600/20 text-teal-300 border border-teal-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0 transition-colors" />
              {!collapsed && (
                <div className="ml-3 flex-1 flex items-center justify-between overflow-hidden">
                  <span className="truncate">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] bg-teal-900/60 text-teal-300 border border-teal-700/50 px-1.5 py-0.5 rounded font-mono font-bold">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40">
        {!collapsed ? (
          <div className="flex items-center space-x-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0"></span>
            <div className="text-xs">
              <p className="text-slate-300 font-medium">Model v1.2.0 Active</p>
              <p className="text-slate-500 text-[11px]">Calibrated HistGB Engine</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="Model v1.2.0 Active">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
        )}
      </div>
    </aside>
  );
};
