import { useState, useEffect } from 'react'

function DataSourceManager() {
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(true)
  const [testingProvider, setTestingProvider] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const providersRes = await fetch('/api/stock/providers').catch(e => ({ ok: false, json: () => ({ providers: {} }) }))
      
      let providersData = { providers: {} }
      
      if (providersRes.ok) {
        providersData = await providersRes.json()
      } else {
        console.error('Failed to fetch providers')
      }
      
      const providersList = Object.entries(providersData.providers || {}).map(([key, val]) => ({ id: key, ...val }))
      setProviders(providersList)
    } catch (err) {
      console.error('Fetch error:', err)
      setProviders([])
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async (providerId) => {
    setTestingProvider(providerId)
    try {
      const url = `/api/stock/test?provider=${providerId}`
      const response = await fetch(url, {
        method: 'POST'
      })
      const text = await response.text()
      console.log('Test response:', text)
      
      if (!response.ok) {
        alert('测试失败: ' + text)
        return
      }
      
      try {
        const data = JSON.parse(text)
        alert(data.message || (data.connected ? '连接成功' : '连接失败'))
      } catch (e) {
        alert('测试失败: ' + text)
      }
    } catch (err) {
      alert('测试失败: ' + err.message)
    } finally {
      setTestingProvider(null)
    }
  }

  const providerDescriptions = {
    tushare: { name: 'Tushare', desc: 'A股数据（需要Token）', market: 'A股' },
    akshare: { name: 'AKShare', desc: 'A股/港股/期货（免费）', market: 'A股/港股' },
    baostock: { name: 'BaoStock', desc: 'A股/港股历史数据', market: 'A股/港股' },
    yfinance: { name: 'YFinance', desc: '美股/港股', market: '美股/港股' },
    juhe: { name: '聚合数据', desc: '实时行情+五档盘口（免费额度）', market: 'A股' }
  }

  if (loading) {
    return (
      <div className="datasource-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="datasource-page fade-in">
      <div className="page-header">
        <h1>数据源管理</h1>
        <p>配置和管理股票数据源</p>
      </div>

      <div className="section">
        <h2>数据源</h2>
        <div className="providers-grid">
          {providers.map(provider => {
            const info = providerDescriptions[provider.id] || { name: provider.id, desc: '', market: '' }
            return (
              <div key={provider.id} className="provider-card">
                <div className="provider-header">
                  <h3>{info.name}</h3>
                  <span className={`status ${provider.available ? 'connected' : 'disconnected'}`}>
                    {provider.available ? '● 已安装' : '○ 未安装'}
                  </span>
                </div>
                <p className="provider-desc">{info.desc}</p>
                <p className="provider-market">市场: {info.market}</p>
                <div className="provider-actions">
                  {provider.available && (
                    <button 
                      onClick={() => testConnection(provider.id)} 
                      className="btn btn-secondary"
                      disabled={testingProvider === provider.id}
                    >
                      {testingProvider === provider.id ? '测试中...' : '测试'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default DataSourceManager
