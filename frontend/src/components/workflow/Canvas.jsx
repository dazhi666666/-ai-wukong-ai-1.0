import { useState, useCallback, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Panel,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import StartNode from './nodes/StartNode';
import LLMNode from './nodes/LLMNode';
import EndNode from './nodes/EndNode';
import Toolbar from './Toolbar';
import './Canvas.css';

const nodeTypes = {
  start: StartNode,
  llm: LLMNode,
  end: EndNode
};

let id = 0;
const getId = () => `node_${id++}`;

const CanvasContent = () => {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);

  const onConnect = useCallback(
    (params) => {
      // 验证连接规则
      const sourceNode = nodes.find(n => n.id === params.source);
      const targetNode = nodes.find(n => n.id === params.target);
      
      if (sourceNode?.data?.type === 'end') {
        alert('结束节点不能有输出连接');
        return;
      }
      
      if (targetNode?.data?.type === 'start') {
        alert('开始节点不能有输入连接');
        return;
      }

      setEdges((eds) => addEdge({ ...params, id: `edge_${Date.now()}` }, eds));
    },
    [nodes]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY
      });

      const newNode = {
        id: getId(),
        type,
        position,
        data: {
          label: type === 'start' ? '开始' : type === 'llm' ? 'LLM' : '结束',
          type,
          config: type === 'start' 
            ? { variable_name: 'user_input', default_value: '' }
            : type === 'llm'
            ? { prompt: '请根据以下输入回复：{{start.user_input}}', model: 'deepseek-chat', temperature: 0.7, max_tokens: 2000 }
            : { output_key: 'result' }
        }
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance]
  );

  const onConfigChange = useCallback((nodeId, newConfig) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              config: newConfig
            }
          };
        }
        return node;
      })
    );
  }, []);

  const addNode = useCallback((type) => {
    const position = reactFlowInstance?.screenToFlowPosition({
      x: window.innerWidth / 2,
      y: window.innerHeight / 2
    }) || { x: 100, y: 100 };

    const newNode = {
      id: getId(),
      type,
      position,
      data: {
        label: type === 'start' ? '开始' : type === 'llm' ? 'LLM' : '结束',
        type,
        config: type === 'start' 
          ? { variable_name: 'user_input', default_value: '' }
          : type === 'llm'
          ? { prompt: '请根据以下输入回复：{{start.user_input}}', model: 'deepseek-chat', temperature: 0.7, max_tokens: 2000 }
          : { output_key: 'result' }
      }
    };

    setNodes((nds) => nds.concat(newNode));
  }, [reactFlowInstance]);

  const runWorkflow = useCallback(async () => {
    // 验证工作流
    const startNodes = nodes.filter(n => n.data.type === 'start');
    const endNodes = nodes.filter(n => n.data.type === 'end');
    
    if (startNodes.length === 0) {
      alert('请至少添加一个开始节点');
      return;
    }
    
    if (endNodes.length === 0) {
      alert('请至少添加一个结束节点');
      return;
    }

    setIsRunning(true);
    setExecutionResult(null);

    try {
      // 准备请求数据
      const workflowData = {
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          data: n.data,
          position: n.position
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle
        }))
      };

      // 获取开始节点的输入值
      const startNode = startNodes[0];
      const variableName = startNode.data.config?.variable_name || 'user_input';
      const defaultValue = startNode.data.config?.default_value || '';
      
      const userInput = window.prompt(
        `请输入 "${variableName}" 的值：`,
        defaultValue
      );

      if (userInput === null) {
        setIsRunning(false);
        return;
      }

      const response = await fetch('/api/workflows/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          workflow: workflowData,
          inputs: {
            [variableName]: userInput
          }
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '工作流执行失败');
      }

      const result = await response.json();
      setExecutionResult(result);
      
      // 更新结束节点显示结果
      setNodes((nds) =>
        nds.map((node) => {
          if (node.data.type === 'end') {
            return {
              ...node,
              data: {
                ...node.data,
                preview: result.result
              }
            };
          }
          return node;
        })
      );

    } catch (error) {
      alert(`执行失败: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  }, [nodes, edges]);

  const saveWorkflow = useCallback(async () => {
    const name = window.prompt('请输入工作流名称：', '未命名工作流');
    if (!name) return;

    const workflowData = {
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        data: n.data,
        position: n.position
      })),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle
      }))
    };

    try {
      const response = await fetch('/api/workflows/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name,
          workflow: workflowData
        })
      });

      if (!response.ok) {
        throw new Error('保存失败');
      }

      alert('工作流保存成功！');
    } catch (error) {
      alert(`保存失败: ${error.message}`);
    }
  }, [nodes, edges]);

  const clearCanvas = useCallback(() => {
    if (confirm('确定要清空画布吗？')) {
      setNodes([]);
      setEdges([]);
      setExecutionResult(null);
    }
  }, []);

  const loadWorkflow = useCallback(async () => {
    try {
      const response = await fetch('/api/workflows');
      if (!response.ok) {
        throw new Error('获取工作流列表失败');
      }
      
      const workflows = await response.json();
      
      if (workflows.length === 0) {
        alert('暂无已保存的工作流');
        return;
      }

      // 显示工作流列表供选择
      const workflowList = workflows.map(w => `${w.id}: ${w.name}`).join('\n');
      const selectedId = window.prompt(`请输入工作流 ID 加载:\n\n${workflowList}`);
      
      if (!selectedId) return;

      const workflowResponse = await fetch(`/api/workflows/${selectedId}`);
      if (!workflowResponse.ok) {
        const error = await workflowResponse.json();
        throw new Error(error.detail || '加载工作流失败');
      }

      const workflowData = await workflowResponse.json();
      
      // 加载节点
      const loadedNodes = workflowData.workflow.nodes.map(n => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data
      }));
      
      // 加载边
      const loadedEdges = workflowData.workflow.edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle
      }));

      setNodes(loadedNodes);
      setEdges(loadedEdges);
      setExecutionResult(null);
      
      alert(`工作流 "${workflowData.name}" 加载成功！`);
    } catch (error) {
      alert(`加载失败: ${error.message}`);
    }
  }, []);

  // 为每个节点添加 onConfigChange 回调
  const nodesWithCallbacks = nodes.map(node => ({
    ...node,
    data: {
      ...node.data,
      onConfigChange: (newConfig) => onConfigChange(node.id, newConfig)
    }
  }));

  return (
    <div className="canvas-container">
      <Toolbar
        onAddNode={addNode}
        onRun={runWorkflow}
        onSave={saveWorkflow}
        onLoad={loadWorkflow}
        onClear={clearCanvas}
        isRunning={isRunning}
      />
      <div className="reactflow-wrapper" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodesWithCallbacks}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
          minZoom={0.1}
          maxZoom={2}
          fitView
          attributionPosition="bottom-right"
        >
          <Background color="#e5e7eb" gap={16} />
          <Controls />
          <MiniMap
            nodeStrokeWidth={3}
            zoomable
            pannable
          />
          <Panel position="top-right" className="canvas-panel">
            <div className="canvas-info">
              <span>节点: {nodes.length}</span>
              <span>连接: {edges.length}</span>
            </div>
          </Panel>
        </ReactFlow>
        
        {executionResult && (
          <div className="result-panel">
            <div className="result-header">
              <h4>执行结果</h4>
              <button 
                className="close-btn"
                onClick={() => setExecutionResult(null)}
              >
                ×
              </button>
            </div>
            <div className="result-content">
              <pre>{executionResult.result}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const Canvas = () => {
  return (
    <ReactFlowProvider>
      <CanvasContent />
    </ReactFlowProvider>
  );
};

export default Canvas;
