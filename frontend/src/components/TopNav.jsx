import { useState } from 'react'

function TopNav({ activeTab, isDarkMode, onThemeToggle }) {
  const [breadcrumbs, setBreadcrumbs] = useState(getBreadcrumbs(activeTab))

  function getBreadcrumbs(tab) {
    const map = {
      'chat': ['首页', '对话'],
      'workflow': ['首页', '工作流'],
      'logs': ['首页', '系统日志'],
      'database': ['首页', '数据库管理'],
      'model': ['首页', '系统设置', '模型配置']
    }
    return map[tab] || ['首页']
  }

  return (
    <header className="top-nav">
      <div className="breadcrumb-container">
        <nav className="breadcrumb">
          {getBreadcrumbs(activeTab).map((item, index, arr) => (
            <span key={index} className="breadcrumb-item">
              {index > 0 && <span className="breadcrumb-separator">/</span>}
              <span className={`breadcrumb-text ${index === arr.length - 1 ? 'breadcrumb-active' : ''}`}>
                {item}
              </span>
            </span>
          ))}
        </nav>
      </div>

      <div className="top-nav-actions">
        <button 
          className="theme-toggle"
          onClick={onThemeToggle}
          title={isDarkMode ? '切换到浅色模式' : '切换到深色模式'}
        >
          <div className={`theme-toggle-track ${isDarkMode ? 'theme-toggle-dark' : ''}`}>
            <div className="theme-toggle-thumb">
              {isDarkMode ? <MoonIcon /> : <SunIcon />}
            </div>
          </div>
        </button>

        <button className="notification-btn" title="通知">
          <BellIcon />
          <span className="notification-badge">3</span>
        </button>

        <button className="help-btn" title="帮助">
          <HelpIcon />
        </button>
      </div>
    </header>
  )
}

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/>
      <line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  )
}

function BellIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  )
}

function HelpIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  )
}

export default TopNav
