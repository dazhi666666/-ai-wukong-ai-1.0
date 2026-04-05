import { useState, useEffect, useMemo } from 'react'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const providerConfig = {
  juhe: { name: 'Juhe 聚合数据', bg: '#fef3c7', text: '#92400e', icon: '🔷' },
  tushare: { name: 'Tushare', bg: '#dbeafe', text: '#1e40af', icon: '🔶' },
  akshare: { name: 'AKShare', bg: '#d1fae5', text: '#065f46', icon: '🔹' },
  baostock: { name: 'BaoStock', bg: '#fce7f3', text: '#9d174d', icon: '🔸' },
  other: { name: '其它', bg: '#e5e7eb', text: '#6b7280', icon: '📊' },
}

const DATA_SOURCE_LIST = [
  { id: 'all', name: '全部', icon: '📋' },
  { id: 'juhe', name: 'Juhe 聚合数据', icon: '🔷' },
  { id: 'tushare', name: 'Tushare', icon: '🔶' },
  { id: 'akshare', name: 'AKShare', icon: '🔹' },
  { id: 'baostock', name: 'BaoStock', icon: '🔸' },
  { id: 'other', name: '其它', icon: '📊' },
]

const ICON_REGEX = /^[📈📊📰💬🏠🔧🏭🏢📋🔨🏛️🌏🐉💳🔷🔶🔹🔸]+/

const getProviderInfo = (providerId) => providerConfig[providerId] || providerConfig.other

const stripIcon = (name) => name?.replace(ICON_REGEX, '').trim() || ''

function ToolsConfig() {
  const [tools, setTools] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSource, setSelectedSource] = useState('all')
  const [selectedTool, setSelectedTool] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)

  // 默认测试参数映射
  const DEFAULT_TEST_PARAMS = {
    stock_code: '600519',
    symbol: '600519',
    ticker: '600519',
    date: new Date().toISOString().split('T')[0],
    start_date: new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    days: 30,
    limit: 10,
    weeks: 5,
    months: 5,
    year: 2024,
    quarter: 4,
  }

  const getDefaultParams = (tool) => {
    const params = {}
    if (tool.parameters && tool.parameters.length > 0) {
      tool.parameters.forEach(p => {
        if (DEFAULT_TEST_PARAMS[p.name]) {
          params[p.name] = DEFAULT_TEST_PARAMS[p.name]
        } else if (p.name.includes('code') || p.name.includes('symbol') || p.name.includes('ticker')) {
          params[p.name] = '600519'
        } else if (p.name === 'days' || p.name === 'limit') {
          params[p.name] = 10
        } else if (p.default !== undefined) {
          params[p.name] = p.default
        }
      })
    }
    return params
  }

  const handleTest = async (tool) => {
    setTesting(true)
    setTestResult(null)
    try {
      const params = getDefaultParams(tool)
      const res = await fetch(`${API_URL}/tools/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_id: tool.tool_id, params }),
      })
      const data = await res.json()
      setTestResult(data)
    } catch (err) {
      setTestResult({ success: false, error: err.message })
    } finally {
      setTesting(false)
    }
  }

  useEffect(() => {
    fetchTools()
  }, [])

  // 使用 useMemo 缓存筛选后的工具列表
  const filteredTools = useMemo(() => {
    if (selectedSource === 'all') return tools
    return tools.filter(t => t.data_source === selectedSource || t.category === selectedSource)
  }, [tools, selectedSource])

  // 使用 useMemo 缓存启用数量
  const enabledCount = useMemo(() => tools.filter(t => t.is_enabled).length, [tools])

  // 使用 useMemo 缓存每个数据源的工具数量
  const sourceCounts = useMemo(() => {
    const counts = { all: tools.length }
    DATA_SOURCE_LIST.slice(1).forEach(source => {
      counts[source.id] = tools.filter(t => t.data_source === source.id || t.category === source.id).length
    })
    return counts
  }, [tools])

  const fetchTools = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_URL}/tools`)
      if (res.ok) {
        const data = await res.json()
        setTools(data.tools || [])
      }
    } catch (err) {
      console.error('Failed to fetch tools:', err)
    } finally {
      setLoading(false)
    }
  }

  const toggleToolEnabled = async (toolId, currentEnabled) => {
    try {
      setSaving(true)
      const res = await fetch(`${API_URL}/tools/${toolId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !currentEnabled }),
      })
      if (res.ok) {
        setTools(tools.map(t => 
          t.tool_id === toolId ? { ...t, is_enabled: !currentEnabled } : t
        ))
      }
    } catch (err) {
      console.error('Failed to toggle tool:', err)
    } finally {
      setSaving(false)
    }
  }

  const saveEnabledTools = async (toolIds) => {
    try {
      setSaving(true)
      const res = await fetch(`${API_URL}/tools/enabled`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_ids: toolIds }),
      })
      if (res.ok) {
        const data = await res.json()
        alert(data.message)
        fetchTools()
      }
    } catch (err) {
      console.error('Failed to save enabled tools:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleRefresh = async () => {
    try {
      setLoading(true)
      await fetch(`${API_URL}/tools/refresh`, { method: 'POST' })
      await fetchTools()
    } catch (err) {
      console.error('Failed to refresh tools:', err)
      setLoading(false)
    }
  }

  const openToolDetail = (tool) => {
    setSelectedTool(tool)
    setShowModal(true)
  }

  // 移除旧的 getProviderInfo 和 getEnabledCount 函数，使用 useMemo 替代

  if (loading) {
    return (
      <div className="tools-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="tools-page fade-in">
      {/* 顶部标题区 */}
      <div className="page-header">
        <div className="header-left">
          <h1>工具配置</h1>
          <p className="subtitle">共 {tools.length} 个工具，已启用 {enabledCount} 个</p>
        </div>
        <div className="header-right">
          <button className="btn btn-success" onClick={() => {
            const enabledIds = tools.filter(t => t.is_enabled).map(t => t.tool_id)
            saveEnabledTools(enabledIds)
          }}>
            保存配置
          </button>
          <button className="btn btn-secondary" onClick={handleRefresh}>
            刷新
          </button>
        </div>
      </div>

      {/* 数据源筛选标签栏 */}
      <div className="provider-tabs" style={{ marginBottom: '20px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {DATA_SOURCE_LIST.map(source => {
          const count = sourceCounts[source.id] || 0
          const isActive = selectedSource === source.id
          const config = providerConfig[source.id] || {}
          return (
            <button
              key={source.id}
              className={`category-tab ${isActive ? 'active' : ''}`}
              onClick={() => setSelectedSource(source.id)}
              style={{ 
                backgroundColor: isActive ? config.bg : '#f3f4f6',
                fontWeight: 'bold'
              }}
            >
              {source.icon} {source.name} ({count})
            </button>
          )
        })}
      </div>

      {/* 数据表格 */}
      <div className="tools-table-container">
        <table className="tools-table">
          <thead>
            <tr>
              <th>工具名称</th>
              <th>工具ID</th>
              <th>描述</th>
              <th>数据源</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {filteredTools.map(tool => {
              const providerInfo = getProviderInfo(tool.data_source)
              return (
                <tr key={tool.tool_id}>
                  <td className="tool-name">
                    <span className="tool-icon">{tool.icon}</span>
                    {stripIcon(tool.name) || tool.tool_id}
                  </td>
                  <td className="tool-id">{tool.tool_id}</td>
                  <td className="tool-desc" title={tool.description}>
                    {tool.description?.substring(0, 50)}{tool.description?.length > 50 ? '...' : ''}
                  </td>
                  <td>
                    <span 
                      className="category-tag"
                      style={{ backgroundColor: providerInfo.bg, color: providerInfo.text }}
                    >
                      {providerInfo.icon} {providerInfo.name}
                    </span>
                  </td>
                  <td className="tool-actions">
                    <button 
                      className="link-btn"
                      onClick={() => openToolDetail(tool)}
                    >
                      详情
                    </button>
                    <label className="switch">
                      <input 
                        type="checkbox" 
                        checked={tool.is_enabled || false}
                        onChange={() => toggleToolEnabled(tool.tool_id, tool.is_enabled)}
                        disabled={saving}
                      />
                      <span className="slider"></span>
                    </label>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {filteredTools.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
            暂无工具
          </div>
        )}
      </div>

      {/* 工具详情弹窗 */}
      {showModal && selectedTool && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content tool-detail-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedTool.icon} {stripIcon(selectedTool.name) || selectedTool.tool_id}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-grid">
                <div className="detail-item">
                  <label>ID:</label>
                  <span className="code">{selectedTool.tool_id}</span>
                </div>
                <div className="detail-item">
                  <label>描述:</label>
                  <span>{selectedTool.description || '无'}</span>
                </div>
                <div className="detail-item">
                  <label>数据源:</label>
                  {(() => {
                    const info = getProviderInfo(selectedTool.data_source)
                    return (
                      <span 
                        className="category-tag"
                        style={{ backgroundColor: info.bg, color: info.text }}
                      >
                        {info.icon} {info.name}
                      </span>
                    )
                  })()}
                </div>
                <div className="detail-item">
                  <label>超时时间:</label>
                  <span>{selectedTool.timeout}ms</span>
                </div>
                <div className="detail-item">
                  <label>状态:</label>
                  <span className={`status-badge ${selectedTool.is_online ? 'online' : 'offline'}`}>
                    {selectedTool.is_online ? '🟢 在线' : '⚪ 离线'}
                  </span>
                </div>
              </div>

              {selectedTool.parameters && selectedTool.parameters.length > 0 && (
                <div className="params-section">
                  <h3 className="section-title">参数列表</h3>
                  <table className="params-table">
                    <thead>
                      <tr>
                        <th>参数名</th>
                        <th>类型</th>
                        <th>描述</th>
                        <th>必填</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTool.parameters.map((param, idx) => (
                        <tr key={idx}>
                          <td className="param-name">{param.name}</td>
                          <td className="param-type">{param.type}</td>
                          <td className="param-desc">{param.description}</td>
                          <td className="param-required">
                            {param.required ? '🔴 是' : '⚪ 否'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* 测试结果区域 */}
              {testResult && (
                <div className="params-section" style={{ marginTop: '15px' }}>
                  <h3 className="section-title">
                    测试结果 
                    <span style={{ 
                      marginLeft: '10px', 
                      fontSize: '12px',
                      color: testResult.success ? '#10b981' : '#ef4444' 
                    }}>
                      {testResult.success ? '✅ 成功' : '❌ 失败'}
                    </span>
                  </h3>
                  <div style={{ 
                    background: '#1f2937', 
                    color: '#e5e7eb', 
                    padding: '12px', 
                    borderRadius: '6px',
                    fontSize: '12px',
                    maxHeight: '200px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all'
                  }}>
                    {testResult.success ? testResult.result : testResult.error}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-secondary" 
                onClick={() => {
                  setShowModal(false)
                  setTestResult(null)
                }}
              >
                关闭
              </button>
              <button 
                className="btn btn-warning" 
                onClick={() => handleTest(selectedTool)}
                disabled={testing}
                style={{ marginRight: '8px' }}
              >
                {testing ? '测试中...' : '🧪 测试'}
              </button>
              <button className="btn btn-primary" onClick={() => {
                toggleToolEnabled(selectedTool.tool_id, selectedTool.is_enabled)
                setShowModal(false)
              }}>
                {selectedTool.is_enabled ? '禁用' : '启用'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ToolsConfig
