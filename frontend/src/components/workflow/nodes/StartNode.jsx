import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import './nodes.css';

const StartNode = ({ data, isConnectable }) => {
  return (
    <div className="node start-node">
      <div className="node-header">
        <div className="node-icon">🚀</div>
        <span className="node-title">{data.label || '开始'}</span>
      </div>
      <div className="node-content">
        <div className="input-group">
          <label>变量名</label>
          <input
            type="text"
            value={data.config?.variable_name || 'user_input'}
            onChange={(e) => {
              if (data.onConfigChange) {
                data.onConfigChange({
                  ...data.config,
                  variable_name: e.target.value
                });
              }
            }}
            className="node-input"
            placeholder="输入变量名"
          />
        </div>
        <div className="input-group">
          <label>默认值</label>
          <input
            type="text"
            value={data.config?.default_value || ''}
            onChange={(e) => {
              if (data.onConfigChange) {
                data.onConfigChange({
                  ...data.config,
                  default_value: e.target.value
                });
              }
            }}
            className="node-input"
            placeholder="默认值（可选）"
          />
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

export default memo(StartNode);
