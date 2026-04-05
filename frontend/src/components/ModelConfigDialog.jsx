import { useState, useEffect } from 'react'
import configApi from '../api/config'

const DEFAULT_FORM_DATA = {
  provider: '',
  model_name: '',
  model_display_name: '',
  api_base: '',
  max_tokens: 4000,
  temperature: 0.7,
  timeout: 180,
  retry_times: 3,
  enabled: true,
  enable_memory: 'full',
  enable_debug: false,
  priority: 0,
  model_category: '',
  description: '',
  input_price_per_1k: 0,
  output_price_per_1k: 0,
  currency: 'CNY',
  is_default: false,
  capability_level: 2,
  suitable_roles: ['both'],
  features: ['tool_calling'],
  recommended_depths: ['快速', '基础', '标准']
}

const CAPABILITY_LEVELS = [
  { value: 1, label: '1级 - 基础模型', desc: '适合快速分析和简单任务' },
  { value: 2, label: '2级 - 标准模型', desc: '适合日常分析和常规任务' },
  { value: 3, label: '3级 - 高级模型', desc: '适合深度分析和复杂推理' },
  { value: 4, label: '4级 - 专业模型', desc: '适合专业级分析和多轮辩论' },
  { value: 5, label: '5级 - 旗舰模型', desc: '最强能力，适合全面分析' }
]

const SUITABLE_ROLES = [
  { value: 'quick_analysis', label: '快速分析', desc: '数据收集、工具调用' },
  { value: 'deep_analysis', label: '深度分析', desc: '推理、决策' },
  { value: 'both', label: '两者都适合', desc: '全能型模型' }
]

const FEATURES = [
  { value: 'tool_calling', label: '工具调用', desc: '必需特性' },
  { value: 'long_context', label: '长上下文', desc: '支持大量历史信息' },
  { value: 'reasoning', label: '强推理能力', desc: '深度分析必需' },
  { value: 'vision', label: '视觉输入', desc: '支持图表分析' },
  { value: 'fast_response', label: '快速响应', desc: '响应速度快' },
  { value: 'cost_effective', label: '成本效益高', desc: '性价比高' }
]

function ModelConfigDialog({ visible, config, providers: externalProviders, onClose, onSave }) {
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formData, setFormData] = useState({ ...DEFAULT_FORM_DATA })

  useEffect(() => {
    if (visible) {
      if (externalProviders && externalProviders.length > 0) {
        setProviders(externalProviders)
      } else {
        loadProviders()
      }
      
      if (config) {
        setFormData({
          ...DEFAULT_FORM_DATA,
          ...config,
          suitable_roles: config.suitable_roles || ['both'],
          features: config.features || ['tool_calling'],
          recommended_depths: config.recommended_depths || ['快速', '基础', '标准']
        })
      } else {
        setFormData({ ...DEFAULT_FORM_DATA })
      }
    }
  }, [visible, config, externalProviders])

  const loadProviders = async () => {
    try {
      const data = await configApi.getActiveProviders()
      setProviders(data)
    } catch (error) {
      console.error('Failed to load providers:', error)
    }
  }

  const handleSave = async () => {
    if (onSave) {
      onSave(formData)
    } else {
      try {
        setSaving(true)
        await configApi.addOrUpdateModel(formData)
        onClose()
      } catch (error) {
        console.error('Failed to save model config:', error)
        alert('保存配置失败')
      } finally {
        setSaving(false)
      }
    }
  }

  if (!visible) return null

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog dialog-large" onClick={e => e.stopPropagation()}>
        <div className="dialog-header">
          <h3>{config ? '编辑模型配置' : '添加模型配置'}</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="dialog-body">
          <div className="form-row">
            <div className="form-group">
              <label>供应商 *</label>
              <select
                className="form-select"
                value={formData.provider}
                onChange={e => setFormData({ ...formData, provider: e.target.value })}
              >
                <option value="">选择供应商</option>
                {providers.map(p => (
                  <option key={p.name} value={p.name}>{p.display_name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>模型代码 *</label>
              <input
                type="text"
                className="form-input"
                value={formData.model_name}
                onChange={e => setFormData({ ...formData, model_name: e.target.value })}
                placeholder="如: gpt-4, deepseek-chat"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>模型显示名称</label>
              <input
                type="text"
                className="form-input"
                value={formData.model_display_name}
                onChange={e => setFormData({ ...formData, model_display_name: e.target.value })}
                placeholder="如: GPT-4 智能对话"
              />
            </div>

            <div className="form-group">
              <label>API基础URL</label>
              <input
                type="text"
                className="form-input"
                value={formData.api_base}
                onChange={e => setFormData({ ...formData, api_base: e.target.value })}
                placeholder="可选，自定义API端点"
              />
            </div>
          </div>

          <div className="form-divider">模型参数</div>

          <div className="form-row">
            <div className="form-group">
              <label>最大Token数</label>
              <input
                type="number"
                className="form-input"
                value={formData.max_tokens}
                onChange={e => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                min={100}
                max={32000}
              />
            </div>

            <div className="form-group">
              <label>温度参数</label>
              <input
                type="number"
                className="form-input"
                value={formData.temperature}
                onChange={e => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                min={0}
                max={2}
                step={0.1}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>超时时间 (秒)</label>
              <input
                type="number"
                className="form-input"
                value={formData.timeout}
                onChange={e => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
                min={10}
                max={300}
              />
            </div>

            <div className="form-group">
              <label>重试次数</label>
              <input
                type="number"
                className="form-input"
                value={formData.retry_times}
                onChange={e => setFormData({ ...formData, retry_times: parseInt(e.target.value) })}
                min={0}
                max={10}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>优先级</label>
              <input
                type="number"
                className="form-input"
                value={formData.priority}
                onChange={e => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                min={0}
                max={100}
              />
              <small className="form-hint">数值越大优先级越高</small>
            </div>

            <div className="form-group">
              <label>货币单位</label>
              <select
                className="form-select"
                value={formData.currency}
                onChange={e => setFormData({ ...formData, currency: e.target.value })}
              >
                <option value="CNY">人民币 (CNY)</option>
                <option value="USD">美元 (USD)</option>
                <option value="EUR">欧元 (EUR)</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>输入价格 (每1K tokens)</label>
              <input
                type="number"
                className="form-input"
                value={formData.input_price_per_1k}
                onChange={e => setFormData({ ...formData, input_price_per_1k: parseFloat(e.target.value) })}
                min={0}
                step={0.0001}
              />
            </div>

            <div className="form-group">
              <label>输出价格 (每1K tokens)</label>
              <input
                type="number"
                className="form-input"
                value={formData.output_price_per_1k}
                onChange={e => setFormData({ ...formData, output_price_per_1k: parseFloat(e.target.value) })}
                min={0}
                step={0.0001}
              />
            </div>
          </div>

          <div className="form-divider">能力配置 (简化版)</div>

          <div className="form-group">
            <label>能力等级</label>
            <select
              className="form-select"
              value={formData.capability_level}
              onChange={e => setFormData({ ...formData, capability_level: parseInt(e.target.value) })}
            >
              {CAPABILITY_LEVELS.map(level => (
                <option key={level.value} value={level.value}>
                  {level.label} - {level.desc}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>适用角色</label>
            <div className="checkbox-group">
              {SUITABLE_ROLES.map(role => (
                <label key={role.value} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.suitable_roles.includes(role.value)}
                    onChange={e => {
                      const roles = e.target.checked
                        ? [...formData.suitable_roles, role.value]
                        : formData.suitable_roles.filter(r => r !== role.value)
                      setFormData({ ...formData, suitable_roles: roles.length ? roles : ['both'] })
                    }}
                  />
                  {role.label}
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>模型特性</label>
            <div className="checkbox-group">
              {FEATURES.map(feature => (
                <label key={feature.value} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.features.includes(feature.value)}
                    onChange={e => {
                      const feats = e.target.checked
                        ? [...formData.features, feature.value]
                        : formData.features.filter(f => f !== feature.value)
                      setFormData({ ...formData, features: feats.length ? feats : ['tool_calling'] })
                    }}
                  />
                  {feature.label}
                </label>
              ))}
            </div>
          </div>

          <div className="form-divider">其他设置</div>

          <div className="form-row">
            <label className="switch-label">
              <input
                type="checkbox"
                checked={formData.enabled}
                onChange={e => setFormData({ ...formData, enabled: e.target.checked })}
              />
              启用模型
            </label>

            <label className="switch-label">
              <input
                type="checkbox"
                checked={formData.is_default}
                onChange={e => setFormData({ ...formData, is_default: e.target.checked })}
              />
              设为默认模型
            </label>
          </div>

          <div className="form-group">
            <label>描述</label>
            <textarea
              className="form-textarea"
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              placeholder="可选，配置描述"
              rows={2}
            />
          </div>
        </div>

        <div className="dialog-footer">
          <button className="btn btn-secondary" onClick={onClose}>取消</button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={saving || !formData.provider || !formData.model_name}
          >
            {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ModelConfigDialog
