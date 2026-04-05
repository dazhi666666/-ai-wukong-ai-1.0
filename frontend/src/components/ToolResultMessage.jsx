import { useState } from 'react'

function isComplexValue(value) {
  return Array.isArray(value) || (typeof value === 'object' && value !== null)
}

function ToolResultMessage({ toolName, content }) {
  const [isExpanded, setIsExpanded] = useState(true)

  let parsedContent = content
  let isJsonContent = false

  try {
    if (typeof content === 'string') {
      parsedContent = JSON.parse(content)
      isJsonContent = isComplexValue(parsedContent)
    } else if (isComplexValue(content)) {
      parsedContent = content
      isJsonContent = true
    }
  } catch {
    parsedContent = content
  }

  const contentStr = isJsonContent
    ? JSON.stringify(parsedContent, null, 2)
    : String(content)
  const contentLines = contentStr.split('\n')
  const shouldTruncate = contentLines.length > 4 || contentStr.length > 500
  const displayedContent =
    shouldTruncate && !isExpanded
      ? contentStr.length > 500
        ? contentStr.slice(0, 500) + '...'
        : contentLines.slice(0, 4).join('\n') + '\n...'
      : contentStr

  return (
    <div className="message tool_result">
      <div className="tool-result-container">
        <div 
          className="tool-result-header"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="tool-result-label">工具结果</span>
          <span className="tool-name">{toolName}</span>
          <span className="tool-expand-icon">
            {isExpanded ? '▲' : '▼'}
          </span>
        </div>

        {isExpanded && (
          <div className="tool-result-content">
            {isJsonContent && parsedContent && typeof parsedContent === 'object' ? (
              <table className="tool-result-table">
                <tbody>
                  {(Array.isArray(parsedContent)
                    ? parsedContent.slice(0, 10)
                    : Object.entries(parsedContent)
                  ).map((item, argIdx) => {
                    const [key, value] = Array.isArray(parsedContent)
                      ? [argIdx, item]
                      : [item[0], item[1]]
                    return (
                      <tr key={argIdx}>
                        <td className="result-key">{key}</td>
                        <td className="result-value">
                          {isComplexValue(value) ? (
                            <code className="result-code">
                              {JSON.stringify(value, null, 2)}
                            </code>
                          ) : (
                            String(value)
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            ) : (
              <pre className="result-text">{displayedContent}</pre>
            )}
          </div>
        )}

        {shouldTruncate && isExpanded && (
          <div 
            className="tool-result-toggle"
            onClick={() => setIsExpanded(false)}
          >
            收起 ▲
          </div>
        )}
      </div>
    </div>
  )
}

export default ToolResultMessage
