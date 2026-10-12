import React from 'react';
import { UserProfile, DiagramTheme } from '../types/api';

interface NavbarProps {
  user: UserProfile | null;
  activeTab: 'editor' | 'benchmark' | 'audit';
  onTabChange: (tab: 'editor' | 'benchmark' | 'audit') => void;
  theme: DiagramTheme;
  onThemeChange: (theme: DiagramTheme) => void;
  onRoleSwitch: (role: 'viewer' | 'analyst' | 'admin') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  activeTab,
  onTabChange,
  theme,
  onThemeChange,
  onRoleSwitch,
}) => {
  return (
    <header className="navbar-container">
      <div className="navbar-brand">
        <div className="brand-logo">ORBIT</div>
        <div className="brand-title">
          <span className="brand-name">Orbit Workbench</span>
          <span className="brand-tag">Editorial Design &amp; Agent Evaluation</span>
        </div>
      </div>

      <nav className="navbar-tabs">
        <button
          className={`tab-btn ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => onTabChange('editor')}
        >
          Studio Editor
        </button>
        <button
          className={`tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
          onClick={() => onTabChange('benchmark')}
        >
          Agent Benchmarks
        </button>
        <button
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => onTabChange('audit')}
        >
          Audit Trail
        </button>
      </nav>

      <div className="navbar-controls">
        <select
          value={theme}
          onChange={(e) => onThemeChange(e.target.value as DiagramTheme)}
          className="theme-select"
          aria-label="Theme"
        >
          <option value="editorial_light">Light Editorial</option>
          <option value="editorial_dark">Dark Editorial</option>
          <option value="blueprint">Blueprint</option>
          <option value="warm_paper">Warm Paper</option>
        </select>

        {user && (
          <div className="user-badge">
            <span className="user-role">{user.roles[0]?.toUpperCase() || 'ANALYST'}</span>
            <span className="user-name">{user.username}</span>
          </div>
        )}

        <div className="role-switchers">
          <button
            className="role-btn"
            onClick={() => onRoleSwitch('analyst')}
            title="Switch to Analyst Role"
          >
            Analyst
          </button>
          <button
            className="role-btn"
            onClick={() => onRoleSwitch('admin')}
            title="Switch to Admin Role"
          >
            Admin
          </button>
          <button
            className="role-btn"
            onClick={() => onRoleSwitch('viewer')}
            title="Switch to Viewer Role"
          >
            Viewer
          </button>
        </div>
      </div>
    </header>
  );
};
