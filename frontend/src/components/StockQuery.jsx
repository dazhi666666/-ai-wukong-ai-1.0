import { useState, useEffect } from 'react'
import AnalysisSettings from './AnalysisSettings'

function StockQuery() {
  const [querySymbol, setQuerySymbol] = useState('000001')
  const [querying, setQuerying] = useState(false)
  const [activeTab, setActiveTab] = useState('quote')
  const [queryResult, setQueryResult] = useState(null)
  
  // 数据源选择（第一行）
  const [selectedProviders, setSelectedProviders] = useState({
    "juhe": true,
    "baostock": true,
    "akshare": false,
    "tushare": false
  })
  
  // 数据类型选择（第二行）
  const [selectedCategories, setSelectedCategories] = useState({
    "📊 行情数据": true,
    "💰 财务数据": true,
    "📈 估值交易": true,
    "🔄 资金数据": true,
    "🌏 场外数据": true,
    "📺 市场数据": true,
    "📰 资讯数据": true
  })

  useEffect(() => {
    // 组件加载时的初始化
  }, [])

  // 切换数据源
  const toggleProvider = (provider) => {
    setSelectedProviders(prev => ({
      ...prev,
      [provider]: !prev[provider]
    }))
  }
  
  // 切换数据类型
  const toggleCategory = (category) => {
    setSelectedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }
  
  // 全选/取消全选数据源
  const toggleAllProviders = (checked) => {
    setSelectedProviders({
      "juhe": checked,
      "baostock": checked,
      "akshare": checked,
      "tushare": checked
    })
  }
  
  // 全选/取消全选数据类型
  const toggleAllCategories = (checked) => {
    setSelectedCategories({
      "📊 行情数据": checked,
      "💰 财务数据": checked,
      "📈 估值交易": checked,
      "🔄 资金数据": checked,
      "🌏 场外数据": checked,
      "📺 市场数据": checked,
      "📰 资讯数据": checked
    })
  }

  const tabGroups = [
    { name: "📊 行情数据", tabs: [
      { id: 'quote', name: '实时行情' },
      { id: 'order_book', name: '五档盘口' },
      { id: 'daily', name: '日线' }
    ]},
    { name: "💰 财务数据", tabs: [
      { id: 'indicator', name: '财务指标' },
      { id: 'income', name: '利润表' },
      { id: 'balance', name: '资产负债表' },
      { id: 'cashflow', name: '现金流量表' }
    ]},
    { name: "📈 估值交易", tabs: [
      { id: 'valuation', name: '估值数据' },
      { id: 'top10', name: '机构持股' },
      { id: 'dividend', name: '分红配送' }
    ]},
    { name: "🔄 资金数据", tabs: [
      { id: 'moneyflow', name: '资金流向' },
      { id: 'margin', name: '融资融券' },
      { id: 'leaderboard', name: '龙虎榜' }
    ]},
    { name: "🌏 场外数据", tabs: [
      { id: 'hsgt', name: '北向资金' }
    ]},
    { name: "📺 市场数据", tabs: [
      { id: 'market', name: '大盘指数' }
    ]},
    { name: "📰 资讯数据", tabs: [
      { id: 'news', name: '股票新闻' },
      { id: 'info', name: '基本信息' }
    ]}
  ]

  const [expandedGroups, setExpandedGroups] = useState({
    "📊 行情数据": true,
    "💰 财务数据": true,
    "📈 估值交易": true,
    "🔄 资金数据": true,
    "🌏 场外数据": true,
    "📺 市场数据": true,
    "📰 资讯数据": true
  })

  const toggleGroup = (groupName) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupName]: !prev[groupName]
    }))
  }

  const hasData = (tabId) => {
    const result = queryResult
    if (!result) return false
    switch(tabId) {
      case 'quote': return !!result?.quote?.symbol || !!result?.quote?.name
      case 'order_book': return !!result?.quote?.order_book
      case 'daily': return result?.daily?.data?.length > 0
      case 'indicator': return result?.indicator?.data?.length > 0 || result?.indicator?.length > 0
      case 'income': return result?.income?.data?.length > 0
      case 'balance': return result?.balance?.data?.length > 0
      case 'cashflow': return result?.cashflow?.data?.length > 0
      case 'valuation': return !!result?.valuation?.data
      case 'top10': return result?.top10?.data?.length > 0
      case 'dividend': return result?.dividend?.data?.length > 0
      case 'moneyflow': return result?.moneyflow?.data?.length > 0
      case 'margin': return result?.margin?.data?.length > 0
      case 'leaderboard': return result?.leaderboard?.data?.length > 0
      case 'hsgt': return result?.hsgt?.data?.length > 0
      case 'market': return !!result?.index_sh || !!result?.index_sz
      case 'news': return result?.news?.data?.length > 0
      case 'info': return !!result?.info
      default: return false
    }
  }

  const handleTabChange = (tab) => {
    setActiveTab(tab)
  }

  const handleQuery = async () => {
    if (!querySymbol.trim()) {
      alert('请输入股票代码')
      return
    }

    setQuerying(true)
    
    try {
      const symbol = querySymbol.trim()
      const requests = []
      
      // ========== 根据选择的数据源和数据类型构建请求 ==========
      
      // --- 聚合数据 (Juhe) ---
      if (selectedProviders.juhe) {
        // 实时行情 + 五档盘口
        if (selectedCategories["📊 行情数据"]) {
          requests.push({ type: 'quote', promise: fetch(`/api/stock/quote?symbol=${symbol}&provider=juhe`) })
        }
        // 大盘指数 - 上证指数
        if (selectedCategories["📺 市场数据"]) {
          requests.push({ type: 'index_sh', promise: fetch(`/api/stock/index?index_type=0&provider=juhe`) })
          requests.push({ type: 'index_sz', promise: fetch(`/api/stock/index?index_type=1&provider=juhe`) })
        }
      }
      
      // --- 资讯数据 (通用) ---
      if (selectedCategories["📰 资讯数据"]) {
        requests.push({ type: 'news', promise: fetch(`/api/news/stock?symbol=${symbol}`) })
      }
      
      // 执行所有请求
      const responses = await Promise.all(requests.map(r => r.promise))
      
      const parseResponse = async (res) => {
        if (res.ok) return await res.json()
        return null
      }
      
      const results = await Promise.all(responses.map(parseResponse))
      
      // 合并结果
      const merged = { symbol, provider: 'merged' }
      
      results.forEach((data, idx) => {
        const type = requests[idx].type
        
        switch(type) {
          case 'quote':
            merged.quote = data?.data || data
            break
          case 'index_sh':
            merged.index_sh = data?.data
            break
          case 'index_sz':
            merged.index_sz = data?.data
            break
          case 'news':
            merged.news = data
            break
        }
      })
      
      console.log('Merged Result:', merged)
      setQueryResult(merged)
      setActiveTab('quote')
    } catch (err) {
      console.error('查询失败:', err)
      alert('查询失败: ' + err.message)
    } finally {
      setQuerying(false)
    }
  }

  const renderQuote = () => {
    const data = queryResult?.quote
    const quote = data?.quote || data?.data || data
    if (!quote) return <p className="no-data">暂无数据</p>

    const fields = [
      { label: '代码', key: 'symbol', key2: 'full_symbol' },
      { label: '名称', key: 'name' },
      { label: '当前价格', key: 'close', key2: '最新价' },
      { label: '涨跌幅', key: 'pct_chg', key2: '涨跌幅', suffix: '%' },
      { label: '涨跌额', key: 'change', key2: '涨跌额' },
      { label: '成交量', key: 'volume', key2: '成交量' },
      { label: '成交额', key: 'amount', key2: '成交额' },
      { label: '最高', key: 'high', key2: '最高' },
      { label: '最低', key: 'low', key2: '最低' },
      { label: '今开', key: 'open', key2: '今开' },
      { label: '昨收', key: 'pre_close', key2: '昨收' },
      { label: '竞买价', key: 'competitive_price' },
      { label: '竞卖价', key: 'reserve_price' },
      { label: '涨量', key: 'price_change_vol' }
    ]

    const kline = quote?.kline

    return (
      <div>
        <div className="quote-grid">
          {fields.map(field => {
            let value = quote[field.key]
            if (value === undefined && field.key2) value = quote[field.key2]
            if (value === undefined) value = '-'
            if (typeof value === 'number' && field.suffix) value = value.toFixed(2) + field.suffix
            if (typeof value === 'number' && !field.suffix && field.key !== 'volume' && field.key !== 'amount') value = value.toFixed(2)
            
            return (
              <div className="quote-item" key={field.key}>
                <span className="quote-label">{field.label}</span>
                <span className="quote-value">{value}</span>
              </div>
            )
          })}
        </div>
        
        {/* K线图 - 显示实际图片 */}
        {kline && (kline.min || kline.day || kline.week || kline.month) && (
          <div style={{ marginTop: '20px', padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
            <h4 style={{ marginBottom: '15px' }}>📈 K线图</h4>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              {kline.day && (
                <div style={{ textAlign: 'center' }}>
                  <p style={{ marginBottom: '5px', fontSize: '12px' }}>日K线</p>
                  <img src={kline.day} alt="日K线" style={{ width: '500px', height: '300px', borderRadius: '4px' }} />
                </div>
              )}
              {kline.min && (
                <div style={{ textAlign: 'center' }}>
                  <p style={{ marginBottom: '5px', fontSize: '12px' }}>分时图</p>
                  <img src={kline.min} alt="分时图" style={{ width: '500px', height: '300px', borderRadius: '4px' }} />
                </div>
              )}
            </div>
            <div style={{ marginTop: '15px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
              {kline.week && (
                <div style={{ textAlign: 'center' }}>
                  <p style={{ marginBottom: '5px', fontSize: '12px' }}>周K线</p>
                  <img src={kline.week} alt="周K线" style={{ width: '250px', height: '150px', borderRadius: '4px' }} />
                </div>
              )}
              {kline.month && (
                <div style={{ textAlign: 'center' }}>
                  <p style={{ marginBottom: '5px', fontSize: '12px' }}>月K线</p>
                  <img src={kline.month} alt="月K线" style={{ width: '250px', height: '150px', borderRadius: '4px' }} />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderOrderBook = () => {
    const data = queryResult?.quote?.order_book
    if (!data) return <p className="no-data">暂无五档盘口数据</p>

    const buy = data.buy || []
    const sell = data.sell || []

    return (
      <div className="order-book">
        <table className="data-table">
          <thead>
            <tr>
              <th>卖量</th>
              <th>卖价</th>
              <th>价格</th>
              <th>买价</th>
              <th>买量</th>
            </tr>
          </thead>
          <tbody>
            {[4, 3, 2, 1, 0].map(i => (
              <tr key={`row-${i}`}>
                <td>{sell[i]?.volume || '-'}</td>
                <td className="sell-price">{sell[i]?.price || '-'}</td>
                <td className="mid-price">{i === 0 ? (buy[0]?.price || '-') : ''}</td>
                <td className="buy-price">{buy[i]?.price || '-'}</td>
                <td>{buy[i]?.volume || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  const renderDaily = () => {
    const data = queryResult?.daily?.data
    if (!data || data.length === 0) return <p className="no-data">暂无日线数据</p>

    return (
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>开盘</th>
              <th>收盘</th>
              <th>最高</th>
              <th>最低</th>
              <th>成交量</th>
              <th>涨跌幅</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 30).map((row, idx) => (
              <tr key={idx}>
                <td>{row.日期 || row.date || '-'}</td>
                <td>{row.开盘 || '-'}</td>
                <td>{row.收盘 || '-'}</td>
                <td>{row.最高 || '-'}</td>
                <td>{row.最低 || '-'}</td>
                <td>{(row.成交量 || 0).toLocaleString()}</td>
                <td>{row.涨跌幅?.toFixed(2) || '-'}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  const renderIndicator = () => {
    const data = queryResult?.indicator?.data || queryResult?.indicator
    if (!data || data.length === 0) return <p className="no-data">暂无财务指标数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderIncome = () => {
    const data = queryResult?.income?.data
    if (!data || data.length === 0) return <p className="no-data">暂无利润表数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderBalance = () => {
    const data = queryResult?.balance?.data
    if (!data || data.length === 0) return <p className="no-data">暂无资产负债表数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderCashflow = () => {
    const data = queryResult?.cashflow?.data
    if (!data || data.length === 0) return <p className="no-data">暂无现金流量表数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderValuation = () => {
    const data = queryResult?.valuation?.data
    if (!data) return <p className="no-data">暂无估值数据</p>
    return (
      <div className="quote-grid">
        <div className="quote-item"><span className="quote-label">市盈率(PE)</span><span className="quote-value">{data.pe_ttm || '-'}</span></div>
        <div className="quote-item"><span className="quote-label">市净率(PB)</span><span className="quote-value">{data.pb_mrq || '-'}</span></div>
        <div className="quote-item"><span className="quote-label">总市值</span><span className="quote-value">{data.total_mv || '-'}</span></div>
      </div>
    )
  }

  const renderTop10 = () => {
    const data = queryResult?.top10?.data
    if (!data || data.length === 0) return <p className="no-data">暂无机构持股数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderDividend = () => {
    const data = queryResult?.dividend?.data
    if (!data || data.length === 0) return <p className="no-data">暂无分红配送数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderMoneyflow = () => {
    const data = queryResult?.moneyflow?.data
    if (!data || data.length === 0) return <p className="no-data">暂无资金流向数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderMargin = () => {
    const data = queryResult?.margin?.data
    if (!data || data.length === 0) return <p className="no-data">暂无融资融券数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderLeaderboard = () => {
    const data = queryResult?.leaderboard?.data
    if (!data || data.length === 0) return <p className="no-data">暂无龙虎榜数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderHsgt = () => {
    const data = queryResult?.hsgt?.data
    if (!data || data.length === 0) return <p className="no-data">暂无北向资金数据（需Tushare Token）</p>
    return <p className="no-data">数据格式需配置Tushare Token</p>
  }

  const renderMarket = () => {
    const indexSH = queryResult?.index_sh
    const indexSZ = queryResult?.index_sz
    
    if (!indexSH && !indexSZ) return <p className="no-data">暂无大盘指数数据</p>
    
    return (
      <div>
        {indexSH && (
          <div style={{ marginBottom: '20px', padding: '15px', background: '#fff5f5', borderRadius: '8px', border: '1px solid #fecaca' }}>
            <h4 style={{ marginBottom: '10px', color: '#dc2626' }}>📈 上证指数</h4>
            <div className="quote-grid">
              <div className="quote-item"><span className="quote-label">当前点位</span><span className="quote-value">{indexSH.close || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">涨跌幅</span><span className="quote-value" style={{ color: (indexSH.pct_chg || 0) >= 0 ? '#dc2626' : '#16a34a' }}>{indexSH.pct_chg || '-'}%</span></div>
              <div className="quote-item"><span className="quote-label">涨跌额</span><span className="quote-value">{indexSH.change || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">今开</span><span className="quote-value">{indexSH.open || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">最高</span><span className="quote-value">{indexSH.high || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">最低</span><span className="quote-value">{indexSH.low || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">昨收</span><span className="quote-value">{indexSH.pre_close || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">成交量</span><span className="quote-value">{indexSH.volume ? (indexSH.volume / 100000000).toFixed(2) + '亿手' : '-'}</span></div>
              <div className="quote-item"><span className="quote-label">成交额</span><span className="quote-value">{indexSH.amount ? (indexSH.amount / 100000000).toFixed(2) + '亿元' : '-'}</span></div>
              <div className="quote-item"><span className="quote-label">涨量</span><span className="quote-value">{indexSH.now_pic || '-'}</span></div>
            </div>
          </div>
        )}
        
        {indexSZ && (
          <div style={{ padding: '15px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
            <h4 style={{ marginBottom: '10px', color: '#16a34a' }}>📉 深证成指</h4>
            <div className="quote-grid">
              <div className="quote-item"><span className="quote-label">当前点位</span><span className="quote-value">{indexSZ.close || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">涨跌幅</span><span className="quote-value" style={{ color: (indexSZ.pct_chg || 0) >= 0 ? '#dc2626' : '#16a34a' }}>{indexSZ.pct_chg || '-'}%</span></div>
              <div className="quote-item"><span className="quote-label">涨跌额</span><span className="quote-value">{indexSZ.change || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">今开</span><span className="quote-value">{indexSZ.open || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">最高</span><span className="quote-value">{indexSZ.high || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">最低</span><span className="quote-value">{indexSZ.low || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">昨收</span><span className="quote-value">{indexSZ.pre_close || '-'}</span></div>
              <div className="quote-item"><span className="quote-label">成交量</span><span className="quote-value">{indexSZ.volume ? (indexSZ.volume / 100000000).toFixed(2) + '亿手' : '-'}</span></div>
              <div className="quote-item"><span className="quote-label">成交额</span><span className="quote-value">{indexSZ.amount ? (indexSZ.amount / 100000000).toFixed(2) + '亿元' : '-'}</span></div>
              <div className="quote-item"><span className="quote-label">涨量</span><span className="quote-value">{indexSZ.now_pic || '-'}</span></div>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderNews = () => {
    const data = queryResult?.news?.data
    if (!data || data.length === 0) return <p className="no-data">暂无股票新闻</p>
    return (
      <div className="news-list">
        {data.slice(0, 10).map((item, idx) => (
          <div key={idx} style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
            <div style={{ fontWeight: 'bold' }}>{item.title || '-'}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>{item.pub_date || '-'} | {item.source || '-'}</div>
          </div>
        ))}
      </div>
    )
  }

  const renderInfo = () => {
    const data = queryResult?.info?.data || queryResult?.info
    if (!data) return <p className="no-data">暂无基本信息</p>
    return (
      <div className="quote-grid">
        <div className="quote-item"><span className="quote-label">股票代码</span><span className="quote-value">{data.code || data.symbol || '-'}</span></div>
        <div className="quote-item"><span className="quote-label">股票名称</span><span className="quote-value">{data.name || '-'}</span></div>
        <div className="quote-item"><span className="quote-label">上市日期</span><span className="quote-value">{data.date || data.list_date || '-'}</span></div>
        <div className="quote-item"><span className="quote-label">交易所</span><span className="quote-value">{data.market || data.exchange || '-'}</span></div>
      </div>
    )
  }

  const renderContent = () => {
    if (!queryResult) return null

    switch (activeTab) {
      case 'quote': return renderQuote()
      case 'order_book': return renderOrderBook()
      case 'daily': return renderDaily()
      case 'indicator': return renderIndicator()
      case 'income': return renderIncome()
      case 'balance': return renderBalance()
      case 'cashflow': return renderCashflow()
      case 'valuation': return renderValuation()
      case 'top10': return renderTop10()
      case 'dividend': return renderDividend()
      case 'moneyflow': return renderMoneyflow()
      case 'margin': return renderMargin()
      case 'leaderboard': return renderLeaderboard()
      case 'hsgt': return renderHsgt()
      case 'market': return renderMarket()
      case 'news': return renderNews()
      case 'info': return renderInfo()
      default: return <p className="no-data">暂无数据</p>
    }
  }

  const allProvidersSelected = Object.values(selectedProviders).every(v => v)
  const allCategoriesSelected = Object.values(selectedCategories).every(v => v)

  return (
    <div className="stock-query-page fade-in">
      <div className="page-header">
        <h1>股票查询</h1>
        <p>查询股票行情、财务指标、资金流向等数据</p>
      </div>

      <div className="query-form">
        <div className="query-row">
          <div className="query-field">
            <label>股票代码:</label>
            <input
              type="text"
              value={querySymbol}
              onChange={e => setQuerySymbol(e.target.value)}
              placeholder="如: 000001, 600000"
              onKeyDown={e => e.key === 'Enter' && handleQuery()}
            />
          </div>
          <button 
            onClick={handleQuery} 
            className="btn btn-primary"
            disabled={querying}
          >
            {querying ? '查询中...' : '查询'}
          </button>
        </div>
      </div>

      {/* 第一行：选择数据源 */}
      <div style={{ margin: '15px 0', padding: '15px', background: '#f0f9ff', borderRadius: '8px', border: '1px solid #bae6_fd' }}>
        <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ fontWeight: 'bold', color: '#0369a1' }}>选择数据源:</label>
          <label style={{ cursor: 'pointer' }}>
            <input type="checkbox" checked={allProvidersSelected} onChange={e => toggleAllProviders(e.target.checked)} />
            全选
          </label>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px' }}>
          {Object.entries(selectedProviders).map(([provider, checked]) => {
            // 只启用 juhe，其他暂时禁用
            const isDisabled = provider !== 'juhe'
            return (
              <label key={provider} style={{ cursor: isDisabled ? 'not-allowed' : 'pointer', opacity: isDisabled ? 0.5 : 1, display: 'flex', alignItems: 'center', gap: '5px' }}>
                <input 
                  type="checkbox" 
                  checked={checked} 
                  onChange={() => !isDisabled && toggleProvider(provider)} 
                  disabled={isDisabled}
                />
                <span>
                  {provider === 'juhe' && '📡 聚合数据 (可用)'}
                  {provider === 'baostock' && '📊 BaoStock (暂不可用)'}
                  {provider === 'akshare' && '📈 AKShare (暂不可用)'}
                  {provider === 'tushare' && '💹 Tushare (需Token)'}
                </span>
              </label>
            )
          })}
        </div>
      </div>

       {/* 第二行：选择数据类型 */}
       <div style={{ margin: '15px 0', padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
         <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
           <label style={{ fontWeight: 'bold' }}>选择数据类型:</label>
           <label style={{ cursor: 'pointer' }}>
             <input type="checkbox" checked={allCategoriesSelected} onChange={e => toggleAllCategories(e.target.checked)} />
             全选
           </label>
         </div>
         <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px' }}>
           {Object.entries(selectedCategories).map(([category, checked]) => (
             <label key={category} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}>
               <input 
                 type="checkbox" 
                 checked={checked} 
                 onChange={() => toggleCategory(category)} 
               />
               {category}
             </label>
           ))}
         </div>
       </div>

       {/* 分析设置 */}
       <AnalysisSettings 
         onSettingsChange={(settings) => {
           console.log('Analysis settings changed:', settings);
           // 这里可以处理设置变化，例如更新某些状态
         }}
       />

       {queryResult && (
        <div className="stock-tabs-wrapper">
          <div className="tabs-container stock-tabs-vertical">
            <div className="tab-groups-container">
              {tabGroups.map(group => (
                <div key={group.name} className="tab-group">
                  <div 
                    className="tab-group-header"
                    onClick={() => toggleGroup(group.name)}
                  >
                    <span>{group.name}</span>
                    <span className="group-toggle">
                      {expandedGroups[group.name] ? '▼' : '▶'}
                    </span>
                  </div>
                  {expandedGroups[group.name] && (
                    <div className="tab-group-content">
                      {group.tabs.map(tab => (
                        <button
                          key={tab.id}
                          className={`tab ${activeTab === tab.id ? 'active' : ''} ${hasData(tab.id) ? 'has-data' : 'no-data'}`}
                          onClick={() => handleTabChange(tab.id)}
                        >
                          <span className="tab-name">{tab.name}</span>
                          <span className={`tab-status ${hasData(tab.id) ? 'success' : 'error'}`}>
                            {hasData(tab.id) ? '✓' : '✗'}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="query-results">
            <div className="result-section">
              <div className="result-header">
                <h3>{tabGroups.flatMap(g => g.tabs).find(t => t.id === activeTab)?.name || activeTab} - {queryResult.symbol}</h3>
              </div>
              {renderContent()}
            </div>
          </div>
        </div>
      )}

      {!queryResult && (
        <div className="empty-state">
          <p>请输入股票代码进行查询</p>
          <p className="hint">选择上方数据源和数据类型，点击查询按钮</p>
        </div>
      )}
    </div>
  )
}

export default StockQuery
