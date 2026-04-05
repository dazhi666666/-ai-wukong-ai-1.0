import { useState, useEffect } from 'react'
import configApi from '../api/config'
import ModelConfigDialog from './ModelConfigDialog'
import ModelCatalogDialog from './ModelCatalogDialog'

const PRESET_PROVIDERS = [
  { name: 'dashscope', display_name: '阿里云百炼', description: '阿里云百炼大模型服务平台，提供通义千问等模型', default_base_url: 'https://dashscope.aliyuncs.com/api/v1', supported_features: ['chat', 'completion', 'embedding', 'function_calling', 'streaming'] },
  { name: '302ai', display_name: '302.AI', description: '302.AI是企业级AI聚合平台', default_base_url: 'https://api.302.ai/v1', supported_features: ['chat', 'completion', 'embedding', 'image', 'vision', 'function_calling', 'streaming'], is_aggregator: true },
  { name: 'deepseek', display_name: 'DeepSeek', description: 'DeepSeek提供高性能的AI推理服务', default_base_url: 'https://api.deepseek.com', supported_features: ['chat', 'completion', 'function_calling', 'streaming'] },
  { name: 'openai', display_name: 'OpenAI', description: 'OpenAI是人工智能领域的领先公司，提供GPT系列模型', default_base_url: 'https://api.openai.com/v1', supported_features: ['chat', 'completion', 'embedding', 'image', 'vision', 'function_calling', 'streaming'] },
  { name: 'anthropic', display_name: 'Anthropic', description: 'Anthropic专注于AI安全研究，提供Claude系列模型', default_base_url: 'https://api.anthropic.com', supported_features: ['chat', 'completion', 'function_calling', 'streaming'] },
  { name: 'google', display_name: 'Google AI', description: 'Google的人工智能平台，提供Gemini系列模型', default_base_url: 'https://generativelanguage.googleapis.com/v1beta', supported_features: ['chat', 'completion', 'embedding', 'vision', 'function_calling', 'streaming'] },
  { name: 'azure', display_name: 'Azure OpenAI', description: 'Microsoft Azure平台上的OpenAI服务', default_base_url: 'https://your-resource.openai.azure.com', supported_features: ['chat', 'completion', 'embedding', 'function_calling', 'streaming'] },
  { name: 'zhipu', display_name: '智谱AI', description: '智谱AI提供GLM系列中文大模型', default_base_url: 'https://open.bigmodel.cn/api/paas/v4', supported_features: ['chat', 'completion', 'embedding', 'function_calling', 'streaming'] },
  { name: 'baidu', display_name: '百度智能云', description: '百度提供的文心一言等AI服务', default_base_url: 'https://aip.baidubce.com', supported_features: ['chat', 'completion', 'embedding', 'streaming'] },
  { name: 'moonshot', display_name: '月之暗面 (Moonshot)', description: '月之暗面提供Kimi系列大模型服务', default_base_url: 'https://api.moonshot.cn/v1', supported_features: ['chat', 'completion', 'function_calling', 'streaming'] },
  { name: 'minimax', display_name: 'MiniMax', description: 'MiniMax提供文本生成服务', default_base_url: 'https://api.minimax.chat/v1', supported_features: ['chat', 'completion', 'embedding', 'streaming'] },
  { name: 'openrouter', display_name: 'OpenRouter', description: 'OpenRouter是AI模型的统一聚合平台', default_base_url: 'https://openrouter.ai/api/v1', supported_features: ['chat', 'completion', 'embedding', 'image', 'vision', 'function_calling', 'streaming'], is_aggregator: true },
]

function ProviderManager({ onSuccess, onSelectModel }) {
  const [providers, setProviders] = useState([])
  const [models, setModels] = useState([])
  const [catalogs, setCatalogs] = useState({})
  const [loading, setLoading] = useState(true)
  const [showDialog, setShowDialog] = useState(false)
  const [showModelDialog, setShowModelDialog] = useState(false)
  const [showCatalogDialog, setShowCatalogDialog] = useState(false)
  const [editingProvider, setEditingProvider] = useState(null)
  const [editingModel, setEditingModel] = useState(null)
  const [selectedProviderForCatalog, setSelectedProviderForCatalog] = useState(null)
  const [expandedProvider, setExpandedProvider] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    default_base_url: '',
    api_key: '',
    api_secret: '',
    supported_features: [],
    is_active: true,
    is_aggregator: false
  })
  const [selectedPreset, setSelectedPreset] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      let catalogsData = []
      try {
        catalogsData = await configApi.getModelCatalog()
      } catch (e) {
        console.log('No catalog data')
      }
      
      const providersData = await configApi.getProviders()
      const modelsData = await configApi.getModels()
      
      setProviders(providersData || [])
      setModels(modelsData || [])
      
      const catalogsObj = {}
      if (Array.isArray(catalogsData)) {
        catalogsData.forEach(cat => {
          catalogsObj[cat.provider] = cat.models || []
        })
      }
      setCatalogs(catalogsObj)
    } catch (error) {
      console.error('Failed to load data:', error)
      setProviders([])
      setModels([])
      setCatalogs({})
    } finally {
      setLoading(false)
    }
  }

  const getCatalogByProvider = (providerName) => {
    return catalogs[providerName] || []
  }

  const getModelsByProvider = (providerName) => {
    return models.filter(m => m.provider === providerName)
  }

  const handleOpenCatalog = (provider) => {
    setSelectedProviderForCatalog(provider)
    setShowCatalogDialog(true)
  }

  const handleCatalogSaved = () => {
    loadData()
  }

  const handleInitPresets = async () => {
    try {
      setLoading(true)
      await configApi.initPresetProviders()
      try {
        await configApi.initModelCatalog()
      } catch (e) {
        console.log('Init catalog skipped')
      }
      await loadData()
    } catch (error) {
      console.error('Failed to init presets:', error)
      setLoading(false)
    }
  }

  const handlePresetChange = (presetName) => {
    setSelectedPreset(presetName)
    if (!presetName) return
    
    const preset = PRESET_PROVIDERS.find(p => p.name === presetName)
    if (preset) {
      setFormData({
        ...preset,
        api_key: '',
        api_secret: '',
        is_active: true
      })
    }
  }

  const handleEdit = (provider) => {
    setEditingProvider(provider)
    setSelectedPreset('')
    setFormData({
      name: provider.name,
      display_name: provider.display_name || '',
      description: provider.description || '',
      default_base_url: provider.default_base_url || '',
      api_key: provider.api_key || '',
      api_secret: provider.api_secret || '',
      supported_features: provider.supported_features || [],
      is_active: provider.is_active,
      is_aggregator: provider.is_aggregator || false
    })
    setShowDialog(true)
  }

  const handleAdd = () => {
    setEditingProvider(null)
    setSelectedPreset('')
    setFormData({
      name: '',
      display_name: '',
      description: '',
      default_base_url: '',
      api_key: '',
      api_secret: '',
      supported_features: [],
      is_active: true,
      is_aggregator: false
    })
    setShowDialog(true)
  }

  const handleClose = () => {
    setShowDialog(false)
    setEditingProvider(null)
    setSelectedPreset('')
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const payload = { ...formData }
      
      if (payload.api_key && payload.api_key.includes('...')) {
        delete payload.api_key
      }
      if (payload.api_secret && payload.api_secret.includes('...')) {
        delete payload.api_secret
      }

      if (editingProvider) {
        await configApi.updateProvider(editingProvider.name, payload)
      } else {
        await configApi.addProvider(payload)
      }
      
      await loadData()
      handleClose()
      if (onSuccess) onSuccess()
    } catch (error) {
      console.error('Failed to save provider:', error)
      alert(editingProvider ? '更新厂家失败' : '添加厂家失败')
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (provider) => {
    try {
      await configApi.toggleProvider(provider.name)
      await loadData()
    } catch (error) {
      console.error('Failed to toggle provider:', error)
    }
  }

  const handleDelete = async (provider) => {
    if (!confirm(`确定要删除厂家 "${provider.display_name}" 吗？\n这将同时删除该厂家下的所有模型配置。`)) return
    
    try {
      await configApi.deleteProvider(provider.name)
      await loadData()
    } catch (error) {
      console.error('Failed to delete provider:', error)
      alert('删除厂家失败')
    }
  }

  const handleAddModel = (provider) => {
    setEditingModel(null)
    setFormData(prev => ({
      ...prev,
      provider: provider.name,
      model_name: '',
      model_display_name: '',
      api_base: provider.default_base_url || '',
      max_tokens: 4000,
      temperature: 0.7,
      timeout: 180,
      retry_times: 3,
      enabled: true,
      capability_level: 2,
      suitable_roles: ['both'],
      features: ['tool_calling']
    }))
    setShowModelDialog(true)
  }

  const handleEditModel = (model) => {
    setEditingModel(model)
    setShowModelDialog(true)
  }

  const handleDeleteModel = async (model) => {
    if (!confirm(`确定要删除模型 "${model.model_display_name || model.model_name}" 吗？`)) return
    
    try {
      await configApi.deleteModel(model.provider, model.model_name)
      await loadData()
    } catch (error) {
      console.error('Failed to delete model:', error)
      alert('删除模型失败')
    }
  }

  const handleToggleModel = async (model) => {
    try {
      await configApi.toggleModel(model.id)
      await loadData()
    } catch (error) {
      console.error('Failed to toggle model:', error)
    }
  }

  const handleSetDefaultModel = async (model) => {
    try {
      await configApi.setDefaultModel(model.id)
      await loadData()
    } catch (error) {
      console.error('Failed to set default model:', error)
    }
  }

  const handleModelDialogSave = async (modelData) => {
    try {
      await configApi.addOrUpdateModel(modelData)
      await loadData()
      setShowModelDialog(false)
      setEditingModel(null)
    } catch (error) {
      console.error('Failed to save model:', error)
      alert('保存模型失败')
    }
  }

  const handleQuickAddFromCatalog = async (provider, catalogModel) => {
    try {
      await configApi.addOrUpdateModel({
        provider: provider.name,
        model_name: catalogModel.name,
        model_display_name: catalogModel.display_name,
        description: catalogModel.description,
        max_tokens: catalogModel.max_tokens || 4096,
        temperature: 0.7,
        timeout: 180,
        retry_times: 3,
        enabled: true,
        capability_level: 2,
        input_price_per_1k: catalogModel.input_price_per_1k || 0,
        output_price_per_1k: catalogModel.output_price_per_1k || 0,
        currency: catalogModel.currency || 'CNY',
        suitable_roles: ['both'],
        features: catalogModel.capabilities || ['tool_calling'],
        priority: 0,
        is_default: false
      })
      await loadData()
      alert(`已将 "${catalogModel.display_name}" 添加为模型配置`)
    } catch (error) {
      console.error('Failed to add model from catalog:', error)
      alert('添加失败')
    }
  }

  const handleModelDialogClose = () => {
    setShowModelDialog(false)
    setEditingModel(null)
  }

  const featuresLabels = {
    chat: '对话',
    completion: '补全',
    embedding: '向量化',
    image: '图像生成',
    vision: '图像理解',
    function_calling: '函数调用',
    streaming: '流式输出'
  }

  const capabilityLabels = { 1: '基础', 2: '标准', 3: '高级', 4: '专业', 5: '旗舰' }

  return (
    <div className="provider-manager">
      <div className="section-header">
        <h3>厂家管理</h3>
        <div className="section-actions">
          <button className="btn btn-secondary" onClick={handleInitPresets}>
            初始化预设厂家
          </button>
          <button className="btn btn-primary" onClick={handleAdd}>
            添加厂家
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">加载中...</div>
      ) : providers.length === 0 ? (
        <div className="empty-state">
          <p>暂无厂家配置，请点击"初始化预设厂家"或"添加厂家"</p>
        </div>
      ) : (
        <div className="provider-list">
          {providers.map(provider => {
            const providerModels = getModelsByProvider(provider.name)
            const isExpanded = expandedProvider === provider.name
            
            return (
              <div key={provider.id} className="provider-card">
                <div className="provider-header">
                  <div className="provider-info">
                    <span className="provider-name">{provider.display_name}</span>
                    <span className="provider-id">{provider.name}</span>
                    {provider.is_aggregator && <span className="badge">聚合</span>}
                    {providerModels.length > 0 && (
                      <span className="badge badge-primary">{providerModels.length}个模型</span>
                    )}
                  </div>
                  <div className="provider-status">
                    <label className="switch">
                      <input 
                        type="checkbox" 
                        checked={provider.is_active} 
                        onChange={() => handleToggle(provider)}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                </div>
                
                <div className="provider-body">
                  <p className="provider-desc">{provider.description || '暂无描述'}</p>
                  <div className="provider-features">
                    {provider.supported_features?.map(f => (
                      <span key={f} className="feature-tag">{featuresLabels[f] || f}</span>
                    ))}
                  </div>
                  <div className="provider-url">
                    <small>{provider.default_base_url}</small>
                  </div>
                  <div className="provider-key-status">
                    {provider.has_api_key ? (
                      <span className="key-status configured">已配置API Key</span>
                    ) : (
                      <span className="key-status missing">未配置API Key</span>
                    )}
                  </div>
                </div>

                {providerModels.length > 0 && (
                  <div className="provider-models">
                    <div 
                      className="provider-models-header"
                      onClick={() => setExpandedProvider(isExpanded ? null : provider.name)}
                    >
                      <span>已配置模型 ({providerModels.length})</span>
                      <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
                    </div>
                    {isExpanded && (
                      <div className="provider-models-list">
                        {providerModels.map(model => (
                          <div key={model.id} className="model-item">
                            <div className="model-item-info">
                              <span className="model-item-name">
                                {model.model_display_name || model.model_name}
                              </span>
                              {model.is_default && <span className="badge badge-primary">默认</span>}
                              <span className={`badge ${model.enabled ? 'badge-success' : 'badge-secondary'}`}>
                                {model.enabled ? '启用' : '禁用'}
                              </span>
                              <span className="badge">能力{capabilityLabels[model.capability_level]}</span>
                            </div>
                            <div className="model-item-actions">
                              <button 
                                className="btn btn-sm btn-secondary"
                                onClick={() => handleSetDefaultModel(model)}
                                disabled={model.is_default}
                                title="设为默认"
                              >
                                默认
                              </button>
                              <button 
                                className="btn btn-sm btn-secondary"
                                onClick={() => handleToggleModel(model)}
                              >
                                {model.enabled ? '禁用' : '启用'}
                              </button>
                              <button 
                                className="btn btn-sm btn-secondary"
                                onClick={() => handleEditModel(model)}
                              >
                                编辑
                              </button>
                              <button 
                                className="btn btn-sm btn-danger"
                                onClick={() => handleDeleteModel(model)}
                              >
                                删除
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {getCatalogByProvider(provider.name).length > 0 && (
                  <div className="provider-models">
                    <div 
                      className="provider-models-header"
                      onClick={() => setExpandedProvider(isExpanded ? null : provider.name)}
                    >
                      <span>模型目录 ({getCatalogByProvider(provider.name).length})</span>
                      <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
                    </div>
                    {isExpanded && (
                      <div className="provider-models-list">
                        {getCatalogByProvider(provider.name).map((model, idx) => (
                          <div key={`catalog-${idx}`} className="model-item">
                            <div className="model-item-info">
                              <span className="model-item-name">
                                {model.display_name || model.name}
                              </span>
                              <span className="badge">{model.context_length ? `${(model.context_length/1000).toFixed(0)}K` : ''}</span>
                              <span className="badge">{model.capabilities?.join(', ') || ''}</span>
                            </div>
                            <div className="model-item-actions">
                              <button 
                                className="btn btn-sm btn-primary"
                                onClick={() => handleQuickAddFromCatalog(provider, model)}
                                title="添加到模型配置"
                              >
                                +配置
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                <div className="provider-actions">
                  <button className="btn btn-sm btn-primary" onClick={() => handleAddModel(provider)}>
                    + 添加模型
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleOpenCatalog(provider)}>
                    模型目录
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleEdit(provider)}>
                    编辑
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(provider)}>
                    删除
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showDialog && (
        <div className="dialog-overlay" onClick={handleClose}>
          <div className="dialog" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <h3>{editingProvider ? '编辑厂家' : '添加厂家'}</h3>
              <button className="close-btn" onClick={handleClose}>&times;</button>
            </div>
            
            <div className="dialog-body">
              {!editingProvider && (
                <div className="form-group">
                  <label>快速选择</label>
                  <select 
                    className="form-select"
                    value={selectedPreset}
                    onChange={e => handlePresetChange(e.target.value)}
                  >
                    <option value="">选择预设厂家或手动填写</option>
                    {PRESET_PROVIDERS.map(p => (
                      <option key={p.name} value={p.name}>{p.display_name}</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label>厂家ID *</label>
                <input 
                  type="text" 
                  className="form-input"
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  placeholder="如: openai, deepseek"
                  disabled={!!editingProvider}
                />
              </div>

              <div className="form-group">
                <label>显示名称 *</label>
                <input 
                  type="text" 
                  className="form-input"
                  value={formData.display_name}
                  onChange={e => setFormData({...formData, display_name: e.target.value})}
                  placeholder="如: OpenAI, DeepSeek"
                />
              </div>

              <div className="form-group">
                <label>描述</label>
                <textarea 
                  className="form-textarea"
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  placeholder="厂家简介和特点"
                  rows={2}
                />
              </div>

              <div className="form-group">
                <label>默认API地址</label>
                <input 
                  type="text" 
                  className="form-input"
                  value={formData.default_base_url}
                  onChange={e => setFormData({...formData, default_base_url: e.target.value})}
                  placeholder="https://api.example.com/v1"
                />
              </div>

              <div className="form-group">
                <label>API Key</label>
                <input 
                  type="password" 
                  className="form-input"
                  value={formData.api_key}
                  onChange={e => setFormData({...formData, api_key: e.target.value})}
                  placeholder="输入 API Key（可选）"
                />
                <small className="form-hint">留空则使用环境变量配置</small>
              </div>

              <div className="form-group">
                <label>API Secret</label>
                <input 
                  type="password" 
                  className="form-input"
                  value={formData.api_secret}
                  onChange={e => setFormData({...formData, api_secret: e.target.value})}
                  placeholder="输入 API Secret（可选，某些厂家需要）"
                />
              </div>

              <div className="form-group">
                <label>支持功能</label>
                <div className="checkbox-group">
                  {Object.entries(featuresLabels).map(([key, label]) => (
                    <label key={key} className="checkbox-label">
                      <input 
                        type="checkbox"
                        checked={formData.supported_features.includes(key)}
                        onChange={e => {
                          const features = e.target.checked
                            ? [...formData.supported_features, key]
                            : formData.supported_features.filter(f => f !== key)
                          setFormData({...formData, supported_features: features})
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="switch-label">
                  <input 
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={e => setFormData({...formData, is_active: e.target.checked})}
                  />
                  启用
                </label>
              </div>
            </div>

            <div className="dialog-footer">
              <button className="btn btn-secondary" onClick={handleClose}>取消</button>
              <button 
                className="btn btn-primary" 
                onClick={handleSave}
                disabled={saving || !formData.name || !formData.display_name}
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showModelDialog && (
        <ModelConfigDialog 
          visible={showModelDialog}
          config={editingModel}
          providers={providers}
          onClose={handleModelDialogClose}
          onSave={handleModelDialogSave}
        />
      )}

      {showCatalogDialog && selectedProviderForCatalog && (
        <ModelCatalogDialog
          visible={showCatalogDialog}
          provider={selectedProviderForCatalog}
          onClose={() => {
            setShowCatalogDialog(false)
            setSelectedProviderForCatalog(null)
          }}
          onSave={handleCatalogSaved}
        />
      )}
    </div>
  )
}

export default ProviderManager
