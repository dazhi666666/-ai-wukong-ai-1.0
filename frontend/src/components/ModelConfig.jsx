import { useState, useEffect } from 'react'
import ProviderManager from './ProviderManager'
import configApi from '../api/config'

function ModelConfig() {
  const [activeTab, setActiveTab] = useState('models')
  const [models, setModels] = useState([])
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedModelId, setSelectedModelId] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  
  const [modelParams, setModelParams] = useState({
    max_tokens: 4000,
    temperature: 0.7,
    timeout: 180,
    retry_times: 3,
    enable_memory: 'full',
    enable_debug: false,
  })

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (activeTab === 'models') {
      loadData()
    }
  }, [activeTab])

  useEffect(() => {
    if (models.length > 0 && !selectedModelId) {
      const defaultModel = models.find(m => m.is_default)
      if (defaultModel) {
        setSelectedModelId(defaultModel.id)
        loadModelParams(defaultModel)
      } else if (models.length > 0) {
        setSelectedModelId(models[0].id)
        loadModelParams(models[0])
      }
    } else if (selectedModelId) {
      const model = models.find(m => m.id === selectedModelId)
      if (model) {
        loadModelParams(model)
      }
    }
  }, [models, selectedModelId])

  const loadData = async () => {
    try {
      setLoading(true)
      const [modelsData, providersData] = await Promise.all([
        configApi.getModels(),
        configApi.getProviders()
      ])
      setModels(modelsData)
      setProviders(providersData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadModelParams = (model) => {
    setModelParams({
      max_tokens: model.max_tokens || 4000,
      temperature: model.temperature || 0.7,
      timeout: model.timeout || 180,
      retry_times: model.retry_times || 3,
      enable_memory: model.enable_memory || 'full',
      enable_debug: model.enable_debug || false,
    })
  }

  const handleModelChange = (modelId) => {
    setSelectedModelId(parseInt(modelId))
    setSaved(false)
  }

  const handleParamChange = (field, value) => {
    setModelParams(prev => ({ ...prev, [field]: value }))
    setSaved(false)
  }

  const handleSave = async () => {
    if (!selectedModelId) return
    
    try {
      setSaving(true)
      const model = models.find(m => m.id === selectedModelId)
      await configApi.addOrUpdateModel({
        ...model,
        ...modelParams
      })
      await loadData()
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to save model params:', error)
      alert('保存参数失败')
    } finally {
      setSaving(false)
    }
  }

  const getSelectedModel = () => {
    return models.find(m => m.id === selectedModelId)
  }

  const capabilityLabels = { 1: '基础', 2: '标准', 3: '高级', 4: '专业', 5: '旗舰' }

  const enabledModels = models.filter(m => m.enabled)

  return (
    <div className="model-config-container fade-in">
      <div className="config-header">
        <h2>模型配置</h2>
        <p>配置 LLM 模型的参数、厂家和模型信息</p>
      </div>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'models' ? 'active' : ''}`}
          onClick={() => setActiveTab('models')}
        >
          模型配置
        </button>
        <button 
          className={`tab ${activeTab === 'providers' ? 'active' : ''}`}
          onClick={() => setActiveTab('providers')}
        >
          厂家管理
        </button>
      </div>

      {activeTab === 'models' && (
        <div className="tab-content">
          {loading ? (
            <div className="loading">加载中...</div>
          ) : enabledModels.length === 0 ? (
            <div className="empty-state">
              <p>暂无启用的模型配置</p>
              <p>请先在"厂家管理"中添加模型</p>
            </div>
          ) : (
            <>
              <div className="config-card card-hover">
                <div className="config-section">
                  <h3>当前使用模型</h3>
                  
                  <div className="form-group">
                    <label>选择模型</label>
                    <select
                      value={selectedModelId || ''}
                      onChange={(e) => handleModelChange(e.target.value)}
                      className="form-select"
                    >
                      {enabledModels.map(model => (
                        <option key={model.id} value={model.id}>
                          {model.model_display_name || model.model_name} ({model.provider})
                          {model.is_default ? ' - 默认' : ''}
                        </option>
                      ))}
                    </select>
                  </div>

                  {getSelectedModel() && (
                    <div className="current-model-info">
                      <span className="badge badge-primary">
                        能力{capabilityLabels[getSelectedModel().capability_level] || getSelectedModel().capability_level}
                      </span>
                      {getSelectedModel().is_default && (
                        <span className="badge badge-success">默认模型</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="config-card card-hover">
                <div className="config-section">
                  <h3>模型参数</h3>
                  
                  <div className="form-group">
                    <label>
                      温度 (Temperature)
                      <span className="form-hint">控制输出的随机性，值越高输出越多样化</span>
                    </label>
                    <div className="slider-container">
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={modelParams.temperature}
                        onChange={(e) => handleParamChange('temperature', parseFloat(e.target.value))}
                        className="form-slider"
                      />
                      <span className="slider-value">{modelParams.temperature}</span>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>
                      最大令牌数 (Max Tokens)
                      <span className="form-hint">限制模型生成的最大长度</span>
                    </label>
                    <div className="slider-container">
                      <input
                        type="range"
                        min="100"
                        max="32000"
                        step="100"
                        value={modelParams.max_tokens}
                        onChange={(e) => handleParamChange('max_tokens', parseInt(e.target.value))}
                        className="form-slider"
                      />
                      <span className="slider-value">{modelParams.max_tokens}</span>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>
                      超时时间 (秒)
                      <span className="form-hint">API请求超时时间</span>
                    </label>
                    <div className="slider-container">
                      <input
                        type="range"
                        min="10"
                        max="300"
                        step="10"
                        value={modelParams.timeout}
                        onChange={(e) => handleParamChange('timeout', parseInt(e.target.value))}
                        className="form-slider"
                      />
                      <span className="slider-value">{modelParams.timeout}s</span>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>
                      重试次数
                      <span className="form-hint">请求失败时的重试次数</span>
                    </label>
                    <div className="slider-container">
                      <input
                        type="range"
                        min="0"
                        max="10"
                        step="1"
                        value={modelParams.retry_times}
                        onChange={(e) => handleParamChange('retry_times', parseInt(e.target.value))}
                        className="form-slider"
                      />
                      <span className="slider-value">{modelParams.retry_times}</span>
                    </div>
                  </div>
                </div>

                <div className="config-section">
                  <h3>高级选项</h3>
                  
                  <div className="form-row">
                    <label className="form-label">记忆模式</label>
                    <select
                      className="form-select"
                      value={modelParams.enable_memory}
                      onChange={(e) => handleParamChange('enable_memory', e.target.value)}
                    >
                      <option value="none">不开启记忆</option>
                      <option value="full">全量记忆</option>
                      <option value="enhanced">记忆增强</option>
                    </select>
                  </div>

                  <div className="form-row">
                    <label className="switch-label">
                      <input
                        type="checkbox"
                        checked={modelParams.enable_debug}
                        onChange={(e) => handleParamChange('enable_debug', e.target.checked)}
                      />
                      调试模式
                    </label>
                  </div>
                </div>

                <div className="config-actions">
                  <button 
                    className={`btn btn-primary ripple ${saved ? 'btn-success' : ''}`}
                    onClick={handleSave}
                    disabled={saving || !selectedModelId}
                  >
                    {saving ? '保存中...' : saved ? '已保存' : '保存参数'}
                  </button>
                </div>
              </div>

              <div className="config-card card-hover">
                <div className="config-section">
                  <h3>已配置模型列表</h3>
                  <div className="model-list-compact">
                    {models.map(model => (
                      <div 
                        key={model.id} 
                        className={`model-list-item ${model.id === selectedModelId ? 'selected' : ''}`}
                        onClick={() => handleModelChange(model.id)}
                      >
                        <div className="model-list-item-info">
                          <span className="model-list-item-name">
                            {model.model_display_name || model.model_name}
                          </span>
                          <span className="model-list-item-provider">{model.provider}</span>
                        </div>
                        <div className="model-list-item-badges">
                          {model.is_default && <span className="badge badge-primary">默认</span>}
                          <span className={`badge ${model.enabled ? 'badge-success' : 'badge-secondary'}`}>
                            {model.enabled ? '启用' : '禁用'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'providers' && (
        <div className="tab-content">
          <ProviderManager onSuccess={loadData} />
        </div>
      )}
    </div>
  )
}

export default ModelConfig
