import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import './nodes.css';

const LLMNode = ({ data, isConnectable }) => {
  const models = [
    { value: 'deepseek-chat', label: 'DeepSeek Chat' },
    { value: 'deepseek-coder', label: 'DeepSeek Coder' },
    { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner' }
  ];

  return (
    <div className="node llm-node">
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
        className="handle handle-left"
      />
      <div className="node-header">
        <div className="node-icon">🤖</div>
        <span className="node-title">{data.label || 'LLM'}</span>
      </div>
      <div className="node-content">
        <div className="input-group">
          <label>模型</label>
          <select
            value={data.config?.model || 'deepseek-chat'}
            onChange={(e) => {
              if (data.onConfigChange) {
                data.onConfigChange({
                  ...data.config,
                  model: e.target.value
                });
              }
            }}
            className="node-select"
          >
            {models.map(m => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>
        <div className="input-group">
          <label>Prompt</label>
          <textarea
            value={data.config?.prompt || '{{start.user_input}}'}
            onChange={(e) => {
              if (data.onConfigChange) {
                data.onConfigChange({
                  ...data.config,
                  prompt: e.target.value
                });
              }
            }}
            className="node-textarea"
            rows={4}
            placeholder="输入 Prompt，使用 {{start.user_input}} 引用变量"
          />
          <small className="hint">
            提示: 使用 {'{{start.变量名}}'} 引用开始节点的变量
          </small>
        </div>
        <div className="input-row">
          <div className="input-group half">
            <label>温度</label>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={data.config?.temperature ?? 0.7}
              onChange={(e) => {
                if (data.onConfigChange) {
                  data.onConfigChange({
                    ...data.config,
                    temperature: parseFloat(e.target.value)
                  });
                }
              }}
              className="node-input"
            />
          </div>
          <div className="input-group half">
            <label>最大Token</label>
            <input
              type="number"
              min="1"
              max="8000"
              value={data.config?.max_tokens ?? 2000}
              onChange={(e) => {
                if (data.onConfigChange) {
                  data.onConfigChange({
                    ...data.config,
                    max_tokens: parseInt(e.target.value)
                  });
                }
              }}
              className="node-input"
            />
          </div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={isConnectable}
        className="handle handle-right"
      />
    </div>
  );
};

export default memo(LLMNode);
