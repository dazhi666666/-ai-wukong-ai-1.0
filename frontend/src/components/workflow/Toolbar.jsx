import './Toolbar.css';

const Toolbar = ({ onAddNode, onRun, onSave, onClear, onLoad, isRunning }) => {
  const nodeTypes = [
    { type: 'start', label: '开始节点', icon: '🚀', color: '#10b981' },
    { type: 'llm', label: 'LLM 节点', icon: '🤖', color: '#3b82f6' },
    { type: 'end', label: '结束节点', icon: '🏁', color: '#f59e0b' }
  ];

  const handleDragStart = (e, nodeType) => {
    e.dataTransfer.setData('application/reactflow', nodeType);
    e.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="workflow-toolbar">
      <div className="toolbar-section">
        <h3>节点</h3>
        <div className="node-palette">
          {nodeTypes.map((node) => (
            <div
              key={node.type}
              className="node-item"
              draggable
              onDragStart={(e) => handleDragStart(e, node.type)}
              onClick={() => onAddNode && onAddNode(node.type)}
              style={{ borderLeftColor: node.color }}
            >
              <span className="node-item-icon">{node.icon}</span>
              <span className="node-item-label">{node.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="toolbar-section">
        <h3>操作</h3>
        <div className="toolbar-actions">
          <button
            className="toolbar-btn run-btn"
            onClick={onRun}
            disabled={isRunning}
          >
            <span className="btn-icon">▶️</span>
            <span className="btn-label">{isRunning ? '运行中...' : '运行'}</span>
          </button>
          <button
            className="toolbar-btn save-btn"
            onClick={onSave}
          >
            <span className="btn-icon">💾</span>
            <span className="btn-label">保存</span>
          </button>
          {onLoad && (
            <button
              className="toolbar-btn load-btn"
              onClick={onLoad}
            >
              <span className="btn-icon">📂</span>
              <span className="btn-label">加载</span>
            </button>
          )}
          <button
            className="toolbar-btn clear-btn"
            onClick={onClear}
          >
            <span className="btn-icon">🗑️</span>
            <span className="btn-label">清空</span>
          </button>
        </div>
      </div>

      <div className="toolbar-section">
        <h3>说明</h3>
        <div className="toolbar-help">
          <p>• 拖拽节点到画布</p>
          <p>• 点击节点端口连接</p>
          <p>• 使用 {'{{start.变量名}}'} 引用变量</p>
        </div>
      </div>
    </div>
  );
};

export default Toolbar;
