import { useState } from 'react'

function isComplexValue(value) {
  return Array.isArray(value) || (typeof value === 'object' && value !== null)
}

function ToolCallMessage({ toolName, args, id }) {
  const [isExpanded, setIsExpanded] = useState(true)
  
  let parsedArgs = args
  if (typeof args === 'string') {
    try {
      parsedArgs = JSON.parse(args)
    } catch {
      parsedArgs = {}
    }
  }
  
  const hasArgs = parsedArgs && typeof parsedArgs === 'object' && Object.keys(parsedArgs).length > 0

  return (
    <div className="message tool_call">
      <div className="tool-call-container">
        <div 
          className="tool-call-header"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="tool-call-label">工具调用</span>
          <span className="tool-name">{toolName}</span>
          {id && <code className="tool-id">{id}</code>}
          <span className="tool-expand-icon">
            {isExpanded ? '▲' : '▼'}
          </span>
        </div>
        
        {isExpanded && hasArgs && (
          <div className="tool-call-body">
            <div className="tool-args">
              <table className="tool-args-table">
                <tbody>
                  {Object.entries(parsedArgs).map(([key, value], argIdx) => (
                    <tr key={argIdx}>
                      <td className="arg-key">{key}</td>
                      <td className="arg-value">
                        {isComplexValue(value) ? (
                          <code className="arg-code">{JSON.stringify(value, null, 2)}</code>
                        ) : (
                          String(value)
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {isExpanded && !hasArgs && (
          <div className="tool-call-body">
            <div className="tool-args-empty">无参数</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ToolCallMessage
