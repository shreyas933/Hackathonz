import React from 'react';
import { User } from '../types';
import { clearToken } from '../services/api';
import { Building2, Shield, LogOut, UserCircle } from 'lucide-react';

interface NavbarProps {
  user: User;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  const getRoleBadge = () => {
    switch (user.role) {
      case 'admin':
        return <span className="bg-red-50 text-red-700 border border-red-200 text-xs font-medium px-2 py-0.5 rounded">Admin</span>;
      case 'sales':
        return <span className="bg-blue-50 text-blue-700 border border-blue-200 text-xs font-medium px-2 py-0.5 rounded">Sales Rep</span>;
      case 'finance':
        return <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium px-2 py-0.5 rounded">Finance Rep</span>;
      case 'owner':
        return <span className="bg-purple-50 text-purple-700 border border-purple-200 text-xs font-medium px-2 py-0.5 rounded">Business Owner</span>;
      case 'finance_contact':
        return <span className="bg-cyan-50 text-cyan-700 border border-cyan-200 text-xs font-medium px-2 py-0.5 rounded">Finance Contact</span>;
      case 'subscription_manager':
        return <span className="bg-amber-50 text-amber-700 border border-amber-200 text-xs font-medium px-2 py-0.5 rounded">Subscription Manager</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium px-2 py-0.5 rounded">{user.role}</span>;
    }
  };

  const portalTitle = user.user_type === 'customer' ? 'Customer Portal' : 'Internal Management Portal';

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 bg-slate-900 rounded-md flex items-center justify-center text-white font-bold text-lg">
            B
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-slate-900 text-base">Brightloop SMS</span>
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200 font-mono">v1.0</span>
            </div>
            <p className="text-xs text-slate-500">{portalTitle}</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden md:flex flex-col text-right">
            <span className="text-sm font-medium text-slate-800">{user.full_name}</span>
            <span className="text-xs text-slate-500">{user.email}</span>
          </div>

          <div className="flex items-center space-x-2">
            {getRoleBadge()}
          </div>

          <button
            onClick={() => {
              clearToken();
              onLogout();
            }}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-300 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </header>
  );
};

