import { useState, useEffect } from 'react'

function AgentDetail({ agent, onBack }) {
  const [agentData, setAgentData] = useState(null)
  const [activeTab, setActiveTab] = useState('system')
  const [selectedPrompt, setSelectedPrompt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState('')
  const [testInputs, setTestInputs] = useState({})
  const [variablesExpanded, setVariablesExpanded] = useState(true)

  useEffect(() => {
    if (agent?.id) {
      fetchAgentDetail()
    }
  }, [agent])

  const fetchAgentDetail = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/agents/${agent.id}`)
      const data = await response.json()
      setAgentData(data)
      
      if (data.prompt_details && data.prompt_details.length > 0) {
        const defaultPrompt = data.prompt_details.find(p => p.is_default) || data.prompt_details[0]
        setSelectedPrompt(defaultPrompt)
      }
      
      const inputs = {}
      if (data.input_params) {
        data.input_params.forEach(p => {
          inputs[p.name] = ''
        })
      }
      setTestInputs(inputs)
    } catch (error) {
      console.error('Failed to fetch agent detail:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    setExecuting(true)
    setResult('')
    
    try {
      const response = await fetch(`/api/agents/${agent.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputs: testInputs,
          prompt_version: selectedPrompt?.version_slug
        })
      })
      const data = await response.json()
      setResult(data.result || data.error || JSON.stringify(data))
    } catch (error) {
      setResult('执行失败: ' + error.message)
    } finally {
      setExecuting(false)
    }
  }

  const handleUpdatePrompt = async () => {
    if (!selectedPrompt) return
    
    try {
      const response = await fetch(`/api/agents/${agent.id}/prompts/${selectedPrompt.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system_prompt: selectedPrompt.system_prompt,
          user_prompt: selectedPrompt.user_prompt,
          tool_instructions: selectedPrompt.tool_instructions,
          analysis_requirements: selectedPrompt.analysis_requirements,
          output_format: selectedPrompt.output_format,
          constraints: selectedPrompt.constraints
        })
      })
      const data = await response.json()
      alert(data.message || '更新成功')
    } catch (error) {
      alert('更新失败: ' + error.message)
    }
  }

  const handleUpdateConfig = async () => {
    try {
      const response = await fetch(`/api/agents/${agent.id}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          temperature: agentData.config?.temperature || 0.2,
          max_iterations: agentData.config?.max_iterations || 3,
          timeout: agentData.config?.timeout || 300,
          tools: agentData.config?.tools || []
        })
      })
      const data = await response.json()
      alert(data.message || '更新成功')
    } catch (error) {
      alert('更新失败: ' + error.message)
    }
  }

  if (loading) {
    return (
      <div className="agent-detail-loading">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  if (!agentData) {
    return (
      <div className="agent-detail-error">
        <p>加载失败</p>
        <button onClick={onBack}>返回</button>
      </div>
    )
  }

  const getCategoryLabel = (category) => {
    const map = {
      'analyst': '分析师',
      'researcher': '研究员',
      'trader': '交易员',
      'risk': '风险管理',
      'manager': '管理者'
    }
    return map[category] || category
  }

  const inputParams = agentData.input_params || []
  const outputParams = agentData.output_params || []
  const prompts = agentData.prompt_details || []

  return (
    <div className="agent-detail-container">
      <div className="agent-detail-header">
        <button className="back-btn" onClick={onBack}>← 返回</button>
        <div className="agent-title">
          <span className="agent-icon">{agentData.icon}</span>
          <h2>{agentData.name}</h2>
          <span className="slug">{agentData.slug}</span>
        </div>
      </div>

      <div className="agent-detail-content">
        <div className="left-panel">
          <div className="info-card">
            <h3>基本信息</h3>
            <div className="info-item">
              <label>描述</label>
              <p>{agentData.description}</p>
            </div>
            <div className="info-item">
              <label>分类</label>
              <span className="category-tag">{getCategoryLabel(agentData.category)}</span>
            </div>
          </div>

          <div className="info-card">
            <h3>输入参数</h3>
            {inputParams.length === 0 ? (
              <p className="empty-text">无</p>
            ) : (
              inputParams.map((param, idx) => (
                <div key={idx} className="param-item">
                  <span className="required-mark">{param.required ? '🔴' : ''}</span>
                  <span className="param-name">{param.name}</span>
                  <span className="param-type">{param.type}</span>
                  <span className="param-desc">{param.description}</span>
                </div>
              ))
            )}
          </div>

          <div className="info-card">
            <h3>输出结果</h3>
            {outputParams.length === 0 ? (
              <p className="empty-text">无</p>
            ) : (
              outputParams.map((param, idx) => (
                <div key={idx} className="param-item output">
                  <span className="param-name">{param.name}</span>
                  <span className="param-type">{param.type}</span>
                  <span className="param-desc">{param.description}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="middle-panel">
          <div className="info-card">
            <h3>执行配置</h3>
            <div className="config-item">
              <label>温度参数</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={agentData.config?.temperature || 0.2}
                onChange={(e) => setAgentData({
                  ...agentData,
                  config: { ...agentData.config, temperature: parseFloat(e.target.value) }
                })}
              />
              <span className="hint">标准模式: 0.2</span>
            </div>
            <div className="config-item">
              <label>最大迭代次数</label>
              <input
                type="number"
                min="1"
                max="10"
                value={agentData.config?.max_iterations || 3}
                onChange={(e) => setAgentData({
                  ...agentData,
                  config: { ...agentData.config, max_iterations: parseInt(e.target.value) }
                })}
              />
            </div>
            <div className="config-item">
              <label>超时时间</label>
              <input
                type="number"
                min="30"
                value={agentData.config?.timeout || 300}
                onChange={(e) => setAgentData({
                  ...agentData,
                  config: { ...agentData.config, timeout: parseInt(e.target.value) }
                })}
              />
              <span className="hint">秒</span>
            </div>
            <button className="save-btn" onClick={handleUpdateConfig}>保存配置</button>
          </div>

          <div className="info-card">
            <h3>工具配置</h3>
            <div className="tools-list">
              {(agentData.config?.tools || []).map((tool, idx) => (
                <span key={idx} className="tool-tag">{tool}</span>
              ))}
              {(agentData.config?.tools || []).length === 0 && (
                <p className="empty-text">未绑定工具</p>
              )}
            </div>
          </div>
        </div>

        <div className="right-panel">
          <div className="prompt-card">
            <div className="prompt-header">
              <h3>提示词模板</h3>
              <div className="prompt-actions">
                <button className="debug-btn" onClick={handleExecute} disabled={executing}>
                  🐛 {executing ? '执行中...' : '调试'}
                </button>
                <button className="edit-btn" onClick={handleUpdatePrompt}>✏️ 编辑</button>
              </div>
            </div>

            <select
              className="prompt-version-select"
              value={selectedPrompt?.id || ''}
              onChange={(e) => {
                const prompt = prompts.find(p => p.id === parseInt(e.target.value))
                setSelectedPrompt(prompt)
              }}
            >
              {prompts.map(p => (
                <option key={p.id} value={p.id}>
                  {agentData.name} - {p.version_name} ({p.version_slug})
                </option>
              ))}
            </select>

            <div className="variables-section">
              <button 
                className="variables-toggle"
                onClick={() => setVariablesExpanded(!variablesExpanded)}
              >
                {variablesExpanded ? '▼' : '▶'} 可用变量说明
              </button>
              {variablesExpanded && selectedPrompt?.available_variables && (
                <div className="variables-table">
                  {Object.entries(selectedPrompt.available_variables).map(([name, info]) => (
                    <div key={name} className="variable-item">
                      <span className="var-name">{name}</span>
                      <span className="var-desc">{info.description || ''}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="prompt-tabs">
              {['system', 'user', 'tools', 'requirements', 'output', 'constraints'].map(tab => (
                <button
                  key={tab}
                  className={`prompt-tab ${activeTab === tab ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {{
                    'system': '系统提示词',
                    'user': '用户提示词',
                    'tools': '工具指导',
                    'requirements': '分析要求',
                    'output': '输出格式',
                    'constraints': '约束条件'
                  }[tab]}
                </button>
              ))}
            </div>

            <div className="prompt-editor">
              <textarea
                value={
                  activeTab === 'system' ? selectedPrompt?.system_prompt || '' :
                  activeTab === 'user' ? selectedPrompt?.user_prompt || '' :
                  activeTab === 'tools' ? selectedPrompt?.tool_instructions || '' :
                  activeTab === 'requirements' ? selectedPrompt?.analysis_requirements || '' :
                  activeTab === 'output' ? selectedPrompt?.output_format || '' :
                  selectedPrompt?.constraints || ''
                }
                onChange={(e) => {
                  const field = {
                    'system': 'system_prompt',
                    'user': 'user_prompt',
                    'tools': 'tool_instructions',
                    'requirements': 'analysis_requirements',
                    'output': 'output_format',
                    'constraints': 'constraints'
                  }[activeTab]
                  setSelectedPrompt({ ...selectedPrompt, [field]: e.target.value })
                }}
                rows={12}
              />
            </div>
          </div>

          <div className="test-card">
            <h3>测试执行</h3>
            <div className="test-inputs">
              {inputParams.map((param, idx) => (
                <div key={idx} className="test-input-item">
                  <label>{param.name}</label>
                  <input
                    type="text"
                    value={testInputs[param.name] || ''}
                    onChange={(e) => setTestInputs({ ...testInputs, [param.name]: e.target.value })}
                    placeholder={param.description}
                  />
                </div>
              ))}
            </div>
            {result && (
              <div className="test-result">
                <h4>执行结果</h4>
                <pre>{result}</pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AgentDetail