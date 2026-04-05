import { useState, useEffect } from 'react';

function AnalysisSettings({ onSettingsChange }) {
  const [agentsData, setAgentsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [promptVersion, setPromptVersion] = useState('neutral');
  const [expandedAgent, setExpandedAgent] = useState(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/analysis/stock/v2/agents');
      if (!response.ok) {
        throw new Error('Failed to fetch agents');
      }
      const data = await response.json();
      setAgentsData(data.agents || []);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
      console.error('Error fetching agents:', err);
    }
  };

  const handlePromptChange = (version) => {
    setPromptVersion(version);
    if (onSettingsChange) {
      onSettingsChange({ promptVersion: version });
    }
  };

  const handleAgentDetailToggle = (agentSlug) => {
    setExpandedAgent(expandedAgent === agentSlug ? null : agentSlug);
  };

  if (loading) {
    return (
      <div className="analysis-settings">
        <div className="settings-header">
          <h3>分析设置</h3>
          <p className="loading">正在加载Agent配置...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-settings">
        <div className="settings-header">
          <h3>分析设置</h3>
          <p className="error">加载Agent配置失败: {error}</p>
        </div>
      </div>
    );
  }

  if (agentsData.length === 0) {
    return (
      <div className="analysis-settings">
        <div className="settings-header">
          <h3>分析设置</h3>
          <p className="empty">未找到可用的Agent配置</p>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-settings">
      <div className="settings-header">
        <h3>分析设置</h3>
        <div className="prompt-version-selector">
          <label>分析风格:</label>
          <select 
            value={promptVersion} 
            onChange={(e) => handlePromptChange(e.target.value)}
            className="prompt-version-select"
          >
            <option value="conservative">保守型</option>
            <option value="neutral">中性型</option>
            <option value="aggressive">激进型</option>
          </select>
        </div>
      </div>

      <div className="agents-list">
        {agentsData.map((agent) => (
          <div key={agent.tool_id} className="agent-card">
            <div className="agent-header" onClick={() => handleAgentDetailToggle(agent.tool_id)}>
              <div className="agent-info">
                <span className="agent-icon">{agent.icon || '📊'}</span>
                <div className="agent-details">
                  <h4 className="agent-name">{agent.name}</h4>
                  <p className="agent-description">{agent.description}</p>
                </div>
              </div>
              <div className="agent-toggle">
                {expandedAgent === agent.tool_id ? '▲' : '▼'}
              </div>
            </div>

            {expandedAgent === agent.tool_id && (
              <div className="agent-details-content">
                <div className="agent-config">
                  <div className="config-item">
                    <span className="config-label">温度:</span>
                    <span className="config-value">{agent.config?.temperature}</span>
                  </div>
                  <div className="config-item">
                    <span className="config-label">最大迭代:</span>
                    <span className="config-value">{agent.config?.max_iterations}</span>
                  </div>
                  <div className="config-item">
                    <span className="config-label">超时时间:</span>
                    <span className="config-value">{agent.config?.timeout}s</span>
                  </div>
                </div>

                <div className="agent-tools">
                  <span className="tools-label">绑定工具:</span>
                  <span className="tools-value">
                    {agent.config?.tools?.length > 0 
                      ? agent.config?.tools.map(tool => 
                          <span key={tool} className="tool-tag">{tool}</span>
                        )
                      : <span className="no-tools">无绑定工具</span>
                    }
                  </span>
                </div>

                {agent.available_variables && Object.keys(agent.available_variables).length > 0 && (
                  <div className="agent-variables">
                    <span className="variables-label">可用变量:</span>
                    <div className="variables-list">
                      {Object.entries(agent.available_variables).map(([key, value]) => (
                        <div key={key} className="variable-item">
                          <span className="variable-name">{key}</span>: 
                          <span className="variable-desc">{value.description || ''}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default AnalysisSettings;