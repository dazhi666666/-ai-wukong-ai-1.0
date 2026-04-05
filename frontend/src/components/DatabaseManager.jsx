import { useState, useEffect } from 'react'

function DatabaseManager() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/database/stats')
      if (!response.ok) throw new Error('Failed to fetch database stats')
      const data = await response.json()
      setStats(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const exportDatabase = async () => {
    try {
      const response = await fetch('/api/database/export', {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Export failed')
      const data = await response.json()
      alert(`数据库导出成功！文件: ${data.file}`)
    } catch (err) {
      alert(`导出失败: ${err.message}`)
    }
  }

  const clearConversations = async () => {
    if (!confirm('确定要清空所有对话记录吗？此操作不可恢复！')) return
    try {
      const response = await fetch('/api/database/clear', {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Clear failed')
      alert('对话记录已清空')
      fetchStats()
    } catch (err) {
      alert(`清空失败: ${err.message}`)
    }
  }

  if (loading) {
    return (
      <div className="database-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="database-page">
        <div className="error-container">
          <p className="error-message">错误: {error}</p>
          <button onClick={fetchStats} className="retry-btn">重试</button>
        </div>
      </div>
    )
  }

  return (
    <div className="database-page fade-in">
      <div className="page-header">
        <h1>数据库管理</h1>
        <p>查看和管理数据库数据</p>
      </div>

      <div className="database-stats">
        <div className="stat-card">
          <div className="stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
            </svg>
          </div>
          <div className="stat-content">
            <span className="stat-value">{stats?.conversations || 0}</span>
            <span className="stat-label">对话总数</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </div>
          <div className="stat-content">
            <span className="stat-value">{stats?.messages || 0}</span>
            <span className="stat-label">消息总数</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"/>
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
            </svg>
          </div>
          <div className="stat-content">
            <span className="stat-value">{stats?.db_size || '0 KB'}</span>
            <span className="stat-label">数据库大小</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <div className="stat-content">
            <span className="stat-value">{stats?.tables?.length || 0}</span>
            <span className="stat-label">数据表</span>
          </div>
        </div>
      </div>

      <div className="database-tables">
        <h2>数据表</h2>
        <div className="tables-list">
          {stats?.tables?.map((table) => (
            <div key={table.name} className="table-card">
              <div className="table-header">
                <span className="table-name">{table.name}</span>
                <span className="table-count">{table.count} 条记录</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="database-actions">
        <h2>操作</h2>
        <div className="actions-list">
          <button onClick={exportDatabase} className="action-btn export-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            导出数据库
          </button>
          <button onClick={clearConversations} className="action-btn danger-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            清空对话
          </button>
        </div>
      </div>
    </div>
  )
}

export default DatabaseManager
