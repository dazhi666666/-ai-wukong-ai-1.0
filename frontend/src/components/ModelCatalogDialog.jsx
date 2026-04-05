import { useState, useEffect } from 'react'
import configApi from '../api/config'

const PRESET_MODELS = {
  deepseek: [
    { name: 'deepseek-chat', display_name: 'DeepSeek Chat', description: '通用对话模型', context_length: 64000, max_tokens: 4096, input_price_per_1k: 0, output_price_per_1k: 0, currency: 'CNY', capabilities: ['chat', 'function_calling'] },
    { name: 'deepseek-reasoner', display_name: 'DeepSeek R1', description: '深度推理模型', context_length: 64000, max_tokens: 4096, input_price_per_1k: 0, output_price_per_1k: 0, currency: 'CNY', capabilities: ['chat', 'reasoning'] },
    { name: 'deepseek-coder', display_name: 'DeepSeek Coder', description: '编程模型', context_length: 64000, max_tokens: 4096, input_price_per_1k: 0, output_price_per_1k: 0, currency: 'CNY', capabilities: ['code'] },
  ],
  openai: [
    { name: 'gpt-4o', display_name: 'GPT-4o', description: '最新旗舰多模态', context_length: 128000, max_tokens: 16384, input_price_per_1k: 2.5, output_price_per_1k: 10, currency: 'USD', capabilities: ['chat', 'vision', 'function_calling'] },
    { name: 'gpt-4', display_name: 'GPT-4', description: '经典旗舰', context_length: 8192, max_tokens: 4096, input_price_per_1k: 30, output_price_per_1k: 60, currency: 'USD', capabilities: ['chat', 'function_calling'] },
    { name: 'gpt-3.5-turbo', display_name: 'GPT-3.5 Turbo', description: '性价比最高', context_length: 16385, max_tokens: 4096, input_price_per_1k: 0.0005, output_price_per_1k: 0.0015, currency: 'USD', capabilities: ['chat', 'function_calling'] },
  ],
  anthropic: [
    { name: 'claude-3-5-sonnet-20241022', display_name: 'Claude 3.5 Sonnet', description: '最新旗舰', context_length: 200000, max_tokens: 8192, input_price_per_1k: 3, output_price_per_1k: 15, currency: 'USD', capabilities: ['chat', 'vision', 'function_calling'] },
    { name: 'claude-3-haiku-20240307', display_name: 'Claude 3 Haiku', description: '快速响应', context_length: 200000, max_tokens: 4096, input_price_per_1k: 0.00025, output_price_per_1k: 0.00125, currency: 'USD', capabilities: ['chat', 'vision'] },
  ],
  google: [
    { name: 'gemini-1.5-pro', display_name: 'Gemini 1.5 Pro', description: '旗舰多模态', context_length: 2000000, max_tokens: 8192, input_price_per_1k: 1.25, output_price_per_1k: 5, currency: 'USD', capabilities: ['chat', 'vision', 'long_context'] },
    { name: 'gemini-1.5-flash', display_name: 'Gemini 1.5 Flash', description: '快速多模态', context_length: 1000000, max_tokens: 8192, input_price_per_1k: 0.075, output_price_per_1k: 0.3, currency: 'USD', capabilities: ['chat', 'vision', 'long_context'] },
  ],
  dashscope: [
    { name: 'qwen-turbo', display_name: 'Qwen Turbo', description: '快速版', context_length: 10000, max_tokens: 6000, input_price_per_1k: 0.002, output_price_per_1k: 0.006, currency: 'CNY', capabilities: ['chat', 'function_calling'] },
    { name: 'qwen-plus', display_name: 'Qwen Plus', description: '增强版', context_length: 30000, max_tokens: 6000, input_price_per_1k: 0.02, output_price_per_1k: 0.06, currency: 'CNY', capabilities: ['chat', 'function_calling'] },
    { name: 'qwen-max', display_name: 'Qwen Max', description: '旗舰版', context_length: 30000, max_tokens: 6000, input_price_per_1k: 0.2, output_price_per_1k: 0.6, currency: 'CNY', capabilities: ['chat', 'function_calling'] },
  ],
  zhipu: [
    { name: 'glm-4', display_name: 'GLM-4', description: '旗舰', context_length: 128000, max_tokens: 4096, input_price_per_1k: 0.1, output_price_per_1k: 0.1, currency: 'CNY', capabilities: ['chat', 'function_calling'] },
    { name: 'glm-3-turbo', display_name: 'GLM-3 Turbo', description: '性价比', context_length: 128000, max_tokens: 4096, input_price_per_1k: 0.001, output_price_per_1k: 0.001, currency: 'CNY', capabilities: ['chat'] },
  ],
  moonshot: [
    { name: 'moonshot-v1-8k', display_name: 'Kimi k8', description: '8K上下文', context_length: 8000, max_tokens: 4096, input_price_per_1k: 0.015, output_price_per_1k: 0.015, currency: 'CNY', capabilities: ['chat', 'long_context'] },
    { name: 'moonshot-v1-32k', display_name: 'Kimi k32', description: '32K上下文', context_length: 32000, max_tokens: 4096, input_price_per_1k: 0.03, output_price_per_1k: 0.03, currency: 'CNY', capabilities: ['chat', 'long_context'] },
    { name: 'moonshot-v1-128k', display_name: 'Kimi k128', description: '128K超长上下文', context_length: 128000, max_tokens: 4096, input_price_per_1k: 0.06, output_price_per_1k: 0.06, currency: 'CNY', capabilities: ['chat', 'long_context'] },
  ],
  baidu: [
    { name: 'ernie-4.0-8k', display_name: '文心一言4.0', description: '旗舰', context_length: 8000, max_tokens: 4000, input_price_per_1k: 0.12, output_price_per_1k: 0.12, currency: 'CNY', capabilities: ['chat'] },
    { name: 'ernie-3.5-8k', display_name: '文心一言3.5', description: '性价比', context_length: 8000, max_tokens: 4000, input_price_per_1k: 0.012, output_price_per_1k: 0.012, currency: 'CNY', capabilities: ['chat'] },
  ],
  "302ai": [
    { name: 'openai/gpt-4o', display_name: '302-GPT-4o', description: 'GPT-4o', context_length: 128000, max_tokens: 16384, input_price_per_1k: 2, output_price_per_1k: 8, currency: 'CNY', capabilities: ['chat', 'vision'], original_provider: 'openai', original_model: 'gpt-4o' },
    { name: 'anthropic/claude-3.5-sonnet', display_name: '302-Claude 3.5', description: 'Claude 3.5', context_length: 200000, max_tokens: 8192, input_price_per_1k: 2.5, output_price_per_1k: 12.5, currency: 'CNY', capabilities: ['chat', 'vision'], original_provider: 'anthropic', original_model: 'claude-3.5-sonnet' },
  ],
}

const CAPABILITY_LABELS = {
  chat: '对话', completion: '补全', embedding: '向量化', image: '图像', vision: '视觉', 
  function_calling: '函数', streaming: '流式', code: '编程', reasoning: '推理', long_context: '长文本'
}

function ModelCatalogDialog({ visible, provider, onClose, onSave }) {
  const [models, setModels] = useState([])
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (visible && provider) {
      loadCatalog()
    }
  }, [visible, provider])

  const loadCatalog = async () => {
    try {
      setLoading(true)
      const catalog = await configApi.getProviderModelCatalog(provider.name)
      setModels(catalog.models || [])
    } catch (error) {
      console.log('No existing catalog, using empty')
      setModels([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddModel = () => {
    setModels([...models, {
      name: '',
      display_name: '',
      description: '',
      context_length: 8192,
      max_tokens: 4096,
      input_price_per_1k: 0,
      output_price_per_1k: 0,
      currency: 'CNY',
      capabilities: []
    }])
  }

  const handleRemoveModel = (index) => {
    setModels(models.filter((_, i) => i !== index))
  }

  const handleModelChange = (index, field, value) => {
    const newModels = [...models]
    newModels[index] = { ...newModels[index], [field]: value }
    setModels(newModels)
  }

  const handleUsePresetModels = () => {
    const presetModels = PRESET_MODELS[provider.name]
    if (presetModels) {
      setModels(presetModels)
    } else {
      alert('该厂家暂无预设模型')
    }
  }

  const handleSave = async () => {
    const validModels = models.filter(m => m.name && m.display_name)
    if (validModels.length === 0) {
      alert('请至少添加一个模型')
      return
    }

    try {
      setSaving(true)
      await configApi.saveModelCatalog({
        provider: provider.name,
        provider_name: provider.display_name,
        models: validModels
      })
      onSave()
      onClose()
    } catch (error) {
      console.error('Failed to save catalog:', error)
      alert('保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (!visible) return null

  const isAggregator = provider.is_aggregator

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog dialog-large" onClick={e => e.stopPropagation()}>
        <div className="dialog-header">
          <h3>模型目录 - {provider.display_name}</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="dialog-body">
          <div style={{ marginBottom: '16px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-sm" onClick={handleAddModel}>
              + 手动添加模型
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleUsePresetModels}>
              使用预设模板
            </button>
          </div>

          {loading ? (
            <div className="loading">加载中...</div>
          ) : models.length === 0 ? (
            <div className="empty-state">
              <p>暂无模型目录</p>
              <p>点击"手动添加模型"或"使用预设模板"</p>
            </div>
          ) : (
            <div className="catalog-table">
              <table>
                <thead>
                  <tr>
                    <th>模型标识</th>
                    <th>显示名称</th>
                    <th>上下文</th>
                    <th>输入价</th>
                    <th>输出价</th>
                    <th>能力</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model, index) => (
                    <tr key={index}>
                      <td>
                        <input
                          type="text"
                          className="form-input"
                          value={model.name}
                          onChange={e => handleModelChange(index, 'name', e.target.value)}
                          placeholder="如: gpt-4"
                          disabled={isAggregator}
                        />
                      </td>
                      <td>
                        <input
                          type="text"
                          className="form-input"
                          value={model.display_name}
                          onChange={e => handleModelChange(index, 'display_name', e.target.value)}
                          placeholder="如: GPT-4"
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          className="form-input"
                          value={model.context_length}
                          onChange={e => handleModelChange(index, 'context_length', parseInt(e.target.value))}
                          style={{ width: '80px' }}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          className="form-input"
                          value={model.input_price_per_1k}
                          onChange={e => handleModelChange(index, 'input_price_per_1k', parseFloat(e.target.value))}
                          step="0.0001"
                          style={{ width: '70px' }}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          className="form-input"
                          value={model.output_price_per_1k}
                          onChange={e => handleModelChange(index, 'output_price_per_1k', parseFloat(e.target.value))}
                          step="0.0001"
                          style={{ width: '70px' }}
                        />
                      </td>
                      <td>
                        <select
                          className="form-select"
                          value={model.currency}
                          onChange={e => handleModelChange(index, 'currency', e.target.value)}
                          style={{ width: '70px' }}
                        >
                          <option value="CNY">CNY</option>
                          <option value="USD">USD</option>
                        </select>
                      </td>
                      <td>
                        <button className="btn btn-sm btn-danger" onClick={() => handleRemoveModel(index)}>
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="dialog-footer">
          <button className="btn btn-secondary" onClick={onClose}>取消</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ModelCatalogDialog
