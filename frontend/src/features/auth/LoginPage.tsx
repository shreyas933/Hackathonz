import React, { useState } from 'react';
import { api } from '../../services/api';
import { ShieldCheck, UserCheck, KeyRound, Building, ArrowRight } from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: () => void;
  onNavigateRegister: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onNavigateRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    try {
      await api.login({ email, password });
      onLoginSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoAccount = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex w-12 h-12 bg-slate-900 rounded-lg items-center justify-center text-white font-bold text-2xl shadow-sm mb-3">
          B
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Brightloop SMS
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Subscription Management System: Internal and Customer Portals
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 sm:px-8 shadow-sm border border-slate-200 rounded-lg">
          {errorMessage && (
            <div className="mb-5 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700">
              {errorMessage}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Work Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 flex justify-center py-2.5 px-4 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors shadow-sm"
            >
              {isLoading ? 'Signing In...' : 'Sign In to Portal'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Demo Account Quick Select
              </span>
              <span className="text-xs text-amber-700 font-medium bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                Dev Mode
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => fillDemoAccount('admin@brightloop.com', 'AdminPass123!')}
                className="p-2 border border-slate-200 rounded-md text-left hover:border-slate-400 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-800">
                  <ShieldCheck className="w-3.5 h-3.5 text-red-600" />
                  <span>Admin</span>
                </div>
                <div className="text-[11px] text-slate-500 truncate">admin@brightloop.com</div>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount('sales@brightloop.com', 'SalesPass123!')}
                className="p-2 border border-slate-200 rounded-md text-left hover:border-slate-400 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-800">
                  <UserCheck className="w-3.5 h-3.5 text-blue-600" />
                  <span>Sales Rep</span>
                </div>
                <div className="text-[11px] text-slate-500 truncate">sales@brightloop.com</div>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount('finance@brightloop.com', 'FinancePass123!')}
                className="p-2 border border-slate-200 rounded-md text-left hover:border-slate-400 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-800">
                  <KeyRound className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Finance Rep</span>
                </div>
                <div className="text-[11px] text-slate-500 truncate">finance@brightloop.com</div>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount('owner@acmecorp.com', 'OwnerPass123!')}
                className="p-2 border border-slate-200 rounded-md text-left hover:border-slate-400 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-800">
                  <Building className="w-3.5 h-3.5 text-purple-600" />
                  <span>Customer</span>
                </div>
                <div className="text-[11px] text-slate-500 truncate">owner@acmecorp.com</div>
              </button>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 text-center">
            <button
              type="button"
              onClick={onNavigateRegister}
              className="inline-flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              <span>Register new customer business</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

