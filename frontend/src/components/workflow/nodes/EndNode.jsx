import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import './nodes.css';

const EndNode = ({ data, isConnectable }) => {
  return (
    <div className="node end-node">
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
        className="handle handle-left"
      />
      <div className="node-header">
        <div className="node-icon">🏁</div>
        <span className="node-title">{data.label || '结束'}</span>
      </div>
      <div className="node-content">
        <div className="input-group">
          <label>输出变量名</label>
          <input
            type="text"
            value={data.config?.output_key || 'result'}
            onChange={(e) => {
              if (data.onConfigChange) {
                data.onConfigChange({
                  ...data.config,
                  output_key: e.target.value
                });
              }
            }}
            className="node-input"
            placeholder="结果变量名"
          />
        </div>
        <div className="node-preview">
          <label>输出预览</label>
          <div className="preview-box">
            {data.preview || '等待执行...'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default memo(EndNode);
