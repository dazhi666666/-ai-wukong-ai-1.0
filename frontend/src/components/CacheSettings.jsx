import { useState, useEffect } from 'react'

function CacheSettings() {
  const [cacheStats, setCacheStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const cacheRes = await fetch('/api/cache/stats').catch(e => ({ ok: false, json: () => ({}) }))
      
      if (cacheRes.ok) {
        const cacheData = await cacheRes.json()
        setCacheStats(cacheData)
      }
    } catch (err) {
      console.error('Fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const clearCache = async () => {
    if (!confirm('确定要清除所有缓存吗?')) return
    try {
      const response = await fetch('/api/cache/clear', { method: 'POST' })
      const data = await response.json()
      alert(data.message)
      fetchData()
    } catch (err) {
      alert('清除失败: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="cache-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="cache-page fade-in">
      <div className="page-header">
        <h1>缓存设置</h1>
        <p>配置和管理系统缓存</p>
      </div>

      <div className="section">
        <h2>缓存设置</h2>
        <div className="cache-config">
          <div className="config-row">
            <label>
              <input type="checkbox" checked={cacheStats?.config?.redis_enabled} disabled />
              启用Redis缓存
            </label>
            <span className="config-info">
              {cacheStats?.config?.redis_host}:{cacheStats?.config?.redis_port}
            </span>
          </div>
          <div className="config-row">
            <label>
              <input type="checkbox" checked={cacheStats?.config?.memory_cache_enabled} disabled />
              启用内存缓存
            </label>
            <span className="config-info">
              最大条目: {cacheStats?.config?.memory_cache_max_size}
            </span>
          </div>
        </div>
      </div>

      <div className="section">
        <h2>缓存统计</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">内存缓存</div>
            <div className="stat-value">{cacheStats?.stats?.memory?.size || 0} 条</div>
            <div className="stat-info">命中率: {cacheStats?.stats?.memory?.hit_rate || 0}%</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Redis缓存</div>
            <div className="stat-value">{cacheStats?.stats?.redis?.keys || 0} 条</div>
            <div className="stat-info">
              {cacheStats?.stats?.redis?.available ? '已连接' : '未连接'}
            </div>
          </div>
        </div>
        <button onClick={clearCache} className="btn btn-danger">
          清除所有缓存
        </button>
      </div>
    </div>
  )
}

export default CacheSettings
