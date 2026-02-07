import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function Chat() {
  const [prompt, setPrompt] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!prompt.trim()) {
      setError('请输入您的问题')
      return
    }

    setLoading(true)
    setError('')
    setResponse('')

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          temperature: 0.7,
          max_tokens: 2000
        })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || '请求失败')
      }

      const data = await res.json()
      setResponse(data.response)
    } catch (err) {
      setError(err.message || '发生错误，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setPrompt('')
    setResponse('')
    setError('')
  }

  return (
    <div className="chat-container">
      <form onSubmit={handleSubmit} className="chat-form">
        <div className="input-group">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="请输入您的问题..."
            rows={4}
            disabled={loading}
            className="chat-input"
          />
        </div>
        
        <div className="button-group">
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="submit-btn"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                思考中...
              </>
            ) : (
              '发送'
            )}
          </button>
          
          <button
            type="button"
            onClick={handleClear}
            disabled={loading}
            className="clear-btn"
          >
            清空
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>错误：</strong>{error}
        </div>
      )}

      {response && (
        <div className="response-container">
          <h3>📝 回答</h3>
          <div className="response-content">
            {response.split('\n').map((line, index) => (
              <p key={index}>{line || <br />}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Chat