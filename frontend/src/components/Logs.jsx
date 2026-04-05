import { useState, useEffect } from 'react'

function Logs() {
  const [logs, setLogs] = useState([])
  const [userActions, setUserActions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [refreshInterval, setRefreshInterval] = useState(5000)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [activeTab, setActiveTab] = useState('system')

  useEffect(() => {
    fetchLogs()
    fetchUserActions()
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchLogs()
        fetchUserActions()
      }, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  const fetchLogs = async () => {
    try {
      const response = await fetch('/api/logs')
      if (response.ok) {
        const data = await response.json()
        setLogs(data.logs || [])
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchUserActions = async () => {
    try {
      const response = await fetch('/api/logs/user-actions')
      if (response.ok) {
        const data = await response.json()
        setUserActions(data.logs || [])
      }
    } catch (error) {
      console.error('Failed to fetch user actions:', error)
    }
  }

  const getLevelColor = (level) => {
    const colors = {
      INFO: '#22c55e',
      WARNING: '#f59e0b',
      ERROR: '#ef4444',
      DEBUG: '#6b7280'
    }
    return colors[level] || '#6b7280'
  }

  const filteredLogs = filter === 'all' 
    ? logs 
    : logs.filter(log => log.level === filter)

  const downloadLogs = () => {
    const content = logs.map(log => 
      `${log.timestamp} - ${log.level} - ${log.message}`
    ).join('\n')
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `app-logs-${new Date().toISOString().slice(0,10)}.log`
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadUserActions = () => {
    const content = userActions.map(action => 
      `${action.timestamp} - ${action.user_id} - ${action.action} - ${action.details}`
    ).join('\n')
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `user-actions-${new Date().toISOString().slice(0,10)}.log`
    a.click()
    URL.revokeObjectURL(url)
  }

  const clearLogs = async () => {
    if (!window.confirm('确定要清除系统日志吗？此操作不可恢复。')) return
    
    try {
      await fetch('/api/logs/clear', { method: 'POST' })
      setLogs([])
    } catch (error) {
      console.error('Failed to clear logs:', error)
    }
  }

  const clearUserActions = async () => {
    if (!window.confirm('确定要清除用户操作日志吗？此操作不可恢复。')) return
    
    try {
      await fetch('/api/logs/user-actions/clear', { method: 'POST' })
      setUserActions([])
    } catch (error) {
      console.error('Failed to clear user actions:', error)
    }
  }

  const getActionIcon = (action) => {
    if (action.includes('create') || action.includes('send')) return <MessageIcon />
    if (action.includes('delete')) return <TrashIcon />
    if (action.includes('load') || action.includes('toggle')) return <EyeIcon />
    return <UserIcon />
  }

  return (
    <div className="logs-page">
      <div className="logs-header">
        <div className="logs-title">
          <h2>日志管理</h2>
        </div>
        
        <div className="logs-tabs">
          <button 
            className={`logs-tab ${activeTab === 'system' ? 'active' : ''}`}
            onClick={() => setActiveTab('system')}
          >
            系统日志
          </button>
          <button 
            className={`logs-tab ${activeTab === 'user' ? 'active' : ''}`}
            onClick={() => setActiveTab('user')}
          >
            用户操作
          </button>
        </div>
      </div>

      {activeTab === 'system' && (
        <>
          <div className="logs-actions-bar">
            <div className="logs-filter">
              <label>级别筛选:</label>
              <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                <option value="all">全部</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
                <option value="DEBUG">DEBUG</option>
              </select>
            </div>
            
            <div className="logs-auto-refresh">
              <label>
                <input 
                  type="checkbox" 
                  checked={autoRefresh} 
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                自动刷新
              </label>
              {autoRefresh && (
                <select 
                  value={refreshInterval} 
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                >
                  <option value={3000}>3秒</option>
                  <option value={5000}>5秒</option>
                  <option value={10000}>10秒</option>
                  <option value={30000}>30秒</option>
                </select>
              )}
            </div>
            
            <button className="logs-btn" onClick={fetchLogs} title="刷新">
              <RefreshIcon />
            </button>
            
            <button className="logs-btn" onClick={downloadLogs} title="下载日志">
              <DownloadIcon />
            </button>
            
            <button className="logs-btn logs-btn-danger" onClick={clearLogs} title="清除日志">
              <TrashIcon />
            </button>
          </div>

          <div className="logs-stats">
            <div className="log-stat">
              <span className="log-stat-value">{logs.filter(l => l.level === 'INFO').length}</span>
              <span className="log-stat-label">INFO</span>
            </div>
            <div className="log-stat">
              <span className="log-stat-value" style={{ color: '#f59e0b' }}>{logs.filter(l => l.level === 'WARNING').length}</span>
              <span className="log-stat-label">WARNING</span>
            </div>
            <div className="log-stat">
              <span className="log-stat-value" style={{ color: '#ef4444' }}>{logs.filter(l => l.level === 'ERROR').length}</span>
              <span className="log-stat-label">ERROR</span>
            </div>
            <div className="log-stat">
              <span className="log-stat-value" style={{ color: '#6b7280' }}>{logs.filter(l => l.level === 'DEBUG').length}</span>
              <span className="log-stat-label">DEBUG</span>
            </div>
          </div>

          <div className="logs-container">
            {loading ? (
              <div className="logs-loading">加载中...</div>
            ) : filteredLogs.length === 0 ? (
              <div className="logs-empty">暂无日志记录</div>
            ) : (
              <div className="logs-list">
                {filteredLogs.map((log, index) => (
                  <div key={index} className="log-item">
                    <span className="log-timestamp">{log.timestamp}</span>
                    <span 
                      className="log-level" 
                      style={{ color: getLevelColor(log.level) }}
                    >
                      [{log.level}]
                    </span>
                    <span className="log-module">{log.module}</span>
                    <span className="log-message">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'user' && (
        <>
          <div className="logs-actions-bar">
            <span className="logs-count">{userActions.length} 条操作记录</span>
            
            <div className="logs-auto-refresh">
              <label>
                <input 
                  type="checkbox" 
                  checked={autoRefresh} 
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                自动刷新
              </label>
            </div>
            
            <button className="logs-btn" onClick={fetchUserActions} title="刷新">
              <RefreshIcon />
            </button>
            
            <button className="logs-btn" onClick={downloadUserActions} title="下载">
              <DownloadIcon />
            </button>
            
            <button className="logs-btn logs-btn-danger" onClick={clearUserActions} title="清除">
              <TrashIcon />
            </button>
          </div>

          <div className="logs-container">
            {loading ? (
              <div className="logs-loading">加载中...</div>
            ) : userActions.length === 0 ? (
              <div className="logs-empty">暂无用户操作记录</div>
            ) : (
              <div className="logs-list user-actions-list">
                {userActions.map((action, index) => (
                  <div key={index} className="log-item user-action-item">
                    <span className="log-timestamp">{action.timestamp}</span>
                    <span className="log-action-icon">{getActionIcon(action.action)}</span>
                    <span className="log-action">{action.action}</span>
                    <span className="log-details">{action.details || '-'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function RefreshIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M23 4v6h-6M1 20v-6h6"/>
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
    </svg>
  )
}

function DownloadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3 6 5 6 21 6"/>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    </svg>
  )
}

function MessageIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  )
}

function EyeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  )
}

function UserIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  )
}

export default Logs
