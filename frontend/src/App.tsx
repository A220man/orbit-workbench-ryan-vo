import React, { useState, useEffect } from 'react';
import { DiagramTheme, UserProfile } from './types/api';
import { authService } from './services/auth';
import { Navbar } from './components/Navbar';
import { DiagramEditor } from './components/DiagramEditor';
import { EvaluationDashboard } from './components/EvaluationDashboard';
import { AuditLogView } from './components/AuditLogView';
import './App.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'editor' | 'benchmark' | 'audit'>('editor');
  const [theme, setTheme] = useState<DiagramTheme>('editorial_light');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  const initAuth = async () => {
    try {
      const u = await authService.loginDemo('analyst');
      setUser(u);
    } catch (err: any) {
      setAuthError(`Auth Initialization: ${err.message}`);
    }
  };

  const handleRoleSwitch = async (role: 'viewer' | 'analyst' | 'admin') => {
    try {
      const u = await authService.loginDemo(role);
      setUser(u);
    } catch (err: any) {
      setAuthError(`Role switch failed: ${err.message}`);
    }
  };

  useEffect(() => {
    initAuth();
  }, []);

  return (
    <div className={`app-root theme-${theme}`}>
      <Navbar
        user={user}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        theme={theme}
        onThemeChange={setTheme}
        onRoleSwitch={handleRoleSwitch}
      />

      {authError && (
        <div className="auth-alert">
          <span>{authError}</span>
        </div>
      )}

      <main className="main-content">
        {activeTab === 'editor' && <DiagramEditor theme={theme} />}
        {activeTab === 'benchmark' && <EvaluationDashboard />}
        {activeTab === 'audit' && <AuditLogView />}
      </main>

      <footer className="app-footer">
        <div>Orbit Workbench · Ryan Vo &lt;ryandtvo@gmail.com&gt;</div>
        <div className="footer-links">Editorial Diagram Compiler · OIDC Keycloak Protected</div>
      </footer>
    </div>
  );
};

export default App;
