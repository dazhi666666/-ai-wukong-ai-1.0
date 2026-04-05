import { useState, useEffect } from 'react'

const categoryMap = {
  'all': '全部',
  'analyst': '分析师',
  'researcher': '研究员',
  'trader': '交易员',
  'risk': '风险管理',
  'manager': '管理者'
}

function AgentList({ onSelectAgent }) {
  const [agents, setAgents] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchAgents()
  }, [selectedCategory])

  const fetchAgents = async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    
    try {
      const categoryParam = selectedCategory === 'all' ? '' : `category=${selectedCategory}`
      const response = await fetch(`/api/agents?${categoryParam}`)
      const data = await response.json()
      setAgents(data.agents || [])
      setCategories(data.categories || {})
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    fetchAgents(true)
  }

  const getCategoryCount = (slug) => {
    return categories[slug] || 0
  }

  const getCategorySlug = (name) => {
    const map = {
      '全部': 'all',
      '分析师': 'analyst',
      '研究员': 'researcher',
      '交易员': 'trader',
      '风险管理': 'risk',
      '管理者': 'manager'
    }
    return map[name] || 'all'
  }

  if (loading) {
    return (
      <div className="agent-list-loading">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  return (
    <div className="agent-list-container">
      <div className="agent-list-header">
        <div className="page-header">
          <h1>👤 Agent配置</h1>
          <p>查看和管理智能体配置</p>
        </div>
        <button className="refresh-btn" onClick={handleRefresh} disabled={refreshing}>
          <span className={`refresh-icon ${refreshing ? 'spinning' : ''}`}>🔄</span>
          刷新
        </button>
      </div>

      <div className="category-tabs">
        {Object.keys(categoryMap).map(cat => (
          <button
            key={cat}
            className={`category-tab ${selectedCategory === cat ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            {categoryMap[cat]}
            {cat === 'all' ? '' : (
              <span className="count">({getCategoryCount(cat)})</span>
            )}
          </button>
        ))}
      </div>

      <div className="agent-grid">
        {agents.filter(a => selectedCategory === 'all' || a.category === selectedCategory).map(agent => (
          <div key={agent.id} className="agent-card" onClick={() => onSelectAgent(agent)}>
            <div className="agent-card-header">
              <span className="agent-icon">{agent.icon}</span>
              <div className="agent-title">
                <h3>{agent.name}</h3>
                <span className="version-tag">{agent.version}</span>
              </div>
            </div>
            <div className="agent-card-body">
              <p className="agent-description">{agent.description}</p>
            </div>
            <div className="agent-card-footer">
              <button className="view-detail-btn">查看详情</button>
            </div>
          </div>
        ))}
      </div>

      {agents.length === 0 && (
        <div className="empty-state">
          <p>暂无Agent配置</p>
        </div>
      )}
    </div>
  )
}

export default AgentList