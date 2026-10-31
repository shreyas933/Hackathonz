import React, { useState, useEffect } from 'react';
import { User } from './types';
import { api, clearToken } from './services/api';
import { Navbar } from './components/Navbar';
import { LoginPage } from './features/auth/LoginPage';
import { RegisterPage } from './features/auth/RegisterPage';
import { InternalPortal } from './features/internal/InternalPortal';
import { CustomerPortal } from './features/customer/CustomerPortal';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [authView, setAuthView] = useState<'login' | 'register'>('login');

  const checkAuth = async () => {
    setIsInitializing(true);
    try {
      const user = await api.getMe();
      setCurrentUser(user);
    } catch {
      clearToken();
      setCurrentUser(null);
    } finally {
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogout = () => {
    clearToken();
    setCurrentUser(null);
    setAuthView('login');
  };

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="flex items-center space-x-2 text-xs text-slate-500 font-medium">
          <div className="w-3 h-3 bg-blue-600 rounded-full animate-ping" />
          <span>Initializing Brightloop SMS...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    if (authView === 'register') {
      return (
        <RegisterPage
          onRegisterSuccess={() => checkAuth()}
          onNavigateLogin={() => setAuthView('login')}
        />
      );
    }
    return (
      <LoginPage
        onLoginSuccess={() => checkAuth()}
        onNavigateRegister={() => setAuthView('register')}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar user={currentUser} onLogout={handleLogout} />
      <main className="flex-1">
        {currentUser.user_type === 'customer' ? (
          <CustomerPortal user={currentUser} />
        ) : (
          <InternalPortal user={currentUser} />
        )}
      </main>
    </div>
  );
}

export default App;

