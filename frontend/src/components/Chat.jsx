import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { PlusIcon, ChatIcon, TrashIcon, MenuIcon, EmptyIcon, UserIcon, BotIcon, SendIcon, ThinkIcon, ChevronUpIcon, ChevronDownIcon } from './Icons'

function MarkdownContent({ content }) {
  if (!content) return null
  return <ReactMarkdown>{content}</ReactMarkdown>
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const logUserAction = async (action, details = null) => {
  try {
    await fetch(`${API_URL}/logs/user-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action,
        details: details ? JSON.stringify(details) : null
      })
    })
  } catch (error) {
    console.error('Failed to log user action:', error)
  }
}

function Chat() {
  const [prompt, setPrompt] = useState('')
  const [error, setError] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [conversations, setConversations] = useState([])
  const [showSidebar, setShowSidebar] = useState(true)
  const [thinkMode, setThinkMode] = useState(false)
  const [messagesMap, setMessagesMap] = useState({})
  const [loadingMap, setLoadingMap] = useState({})
  const [summaryGeneratingMap, setSummaryGeneratingMap] = useState({})
  const [expandedReasoning, setExpandedReasoning] = useState({})
  const [modelConfig, setModelConfig] = useState(null)
  const [userScrolledUp, setUserScrolledUp] = useState(false)

  const abortControllersRef = useRef({})
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)

  const messages = conversationId ? (messagesMap[conversationId] || []) : []
  const loading = conversationId ? (loadingMap[conversationId] || false) : false
  const summaryGenerating = conversationId ? (summaryGeneratingMap[conversationId] || false) : false

  useEffect(() => {
    loadConversations()
    loadModelConfig()
  }, [])

  useEffect(() => {
    if (!userScrolledUp) {
      scrollToBottom()
    }
  }, [messages, conversationId])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleScroll = () => {
    const container = messagesContainerRef.current
    if (!container) return
    
    const { scrollTop, scrollHeight, clientHeight } = container
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    
    if (distanceFromBottom > 100) {
      setUserScrolledUp(true)
    } else {
      setUserScrolledUp(false)
    }
  }

  const loadConversations = async () => {
    try {
      const res = await fetch(`${API_URL}/conversations`)
      if (res.ok) {
        const data = await res.json()
        setConversations(data)
      }
    } catch (err) {
      console.error('加载对话列表失败:', err)
    }
  }

  const loadModelConfig = async () => {
    try {
      const res = await fetch(`${API_URL}/config/models/default`)
      if (res.ok) {
        const data = await res.json()
        if (data) {
          setModelConfig(data)
          return
        }
      }
      const res2 = await fetch(`${API_URL}/config/models`)
      if (res2.ok) {
        const data = await res2.json()
        if (data && data.length > 0) {
          const enabled = data.find(m => m.enabled)
          if (enabled) {
            setModelConfig(enabled)
          }
        }
      }
    } catch (err) {
      console.error('加载模型配置失败:', err)
    }
  }

  const createNewConversation = async () => {
    setUserScrolledUp(false)
    try {
      const res = await fetch(`${API_URL}/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      if (res.ok) {
        const data = await res.json()
        setConversationId(data.id)
        setMessagesMap(prev => ({ ...prev, [data.id]: [] }))
        setPrompt('')
        setError('')
        loadConversations()
        logUserAction('create_conversation', { conversation_id: data.id })
      }
    } catch (err) {
      setError('创建对话失败')
    }
  }

  const loadConversation = async (convId) => {
    setUserScrolledUp(false)
    try {
      const res = await fetch(`${API_URL}/conversations/${convId}`)
      if (res.ok) {
        const data = await res.json()
        setConversationId(convId)
        const msgs = data.messages || []
        setMessagesMap(prev => ({ ...prev, [convId]: msgs }))
        setPrompt('')
        setError('')
        logUserAction('load_conversation', { conversation_id: convId, message_count: msgs.length })
      }
    } catch (err) {
      setError('加载对话失败')
    }
  }

  const deleteConversation = async (convId, e) => {
    e.stopPropagation()
    try {
      const res = await fetch(`${API_URL}/conversations/${convId}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        if (conversationId === convId) {
          setConversationId(null)
        }
        setMessagesMap(prev => {
          const next = { ...prev }
          delete next[convId]
          return next
        })
        loadConversations()
        logUserAction('delete_conversation', { conversation_id: convId })
      }
    } catch (err) {
      setError('删除对话失败')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!prompt.trim()) {
      setError('请输入您的问题')
      return
    }

    if (!conversationId) {
      setError('请先选择一个对话或创建新对话')
      return
    }

    const currentConvId = conversationId
    
    setLoadingMap(prev => ({ ...prev, [currentConvId]: true }))
    setError('')

    const abortController = new AbortController()
    abortControllersRef.current[currentConvId] = abortController

    const enableMemory = modelConfig?.enable_memory ?? true
    
    let effectiveConversationId = currentConvId
    if (enableMemory && !currentConvId) {
      const convRes = await fetch(`${API_URL}/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      if (convRes.ok) {
        const convData = await convRes.json()
        effectiveConversationId = convData.id
        setConversationId(convData.id)
        setMessagesMap(prev => ({ ...prev, [convData.id]: [] }))
        loadConversations()
        logUserAction('create_conversation', { conversation_id: convData.id })
      }
    }

    try {
      logUserAction('send_message', { 
        prompt_length: prompt.length, 
        model: thinkMode ? 'deepseek-reasoner' : 'deepseek-chat',
        conversation_id: effectiveConversationId,
        enable_memory: enableMemory
      })
      
      const res = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          conversation_id: effectiveConversationId,
          temperature: 0.7,
          max_tokens: 2000,
          model: thinkMode ? 'deepseek-reasoner' : 'deepseek-chat'
        }),
        signal: abortController.signal
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || '请求失败')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      let fullReasoning = ''

      setMessagesMap(prev => ({
        ...prev,
        [currentConvId]: [...(prev[currentConvId] || []), { role: 'user', content: prompt }]
      }))
      setPrompt('')

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            
            if (data === '[DONE]') continue
            
            try {
              const parsed = JSON.parse(data)
              
              if (parsed.error) {
                throw new Error(parsed.error)
              }
              
              if (parsed.reasoning_content) {
                fullReasoning += parsed.reasoning_content
                setMessagesMap(prev => {
                  const msgs = prev[currentConvId] || []
                  const lastMsg = msgs[msgs.length - 1]
                  if (lastMsg?.role === 'assistant') {
                    return {
                      ...prev,
                      [currentConvId]: [...msgs.slice(0, -1), { 
                        ...lastMsg, 
                        reasoning_content: fullReasoning 
                      }]
                    }
                  }
                  return {
                    ...prev,
                    [currentConvId]: [...msgs, { 
                      role: 'assistant', 
                      content: '',
                      reasoning_content: fullReasoning 
                    }]
                  }
                })
              }
              
              if (parsed.content) {
                fullResponse += parsed.content
                setMessagesMap(prev => {
                  const msgs = prev[currentConvId] || []
                  const lastMsg = msgs[msgs.length - 1]
                  if (lastMsg?.role === 'assistant') {
                    return {
                      ...prev,
                      [currentConvId]: [...msgs.slice(0, -1), { 
                        ...lastMsg, 
                        content: fullResponse,
                        reasoning_content: fullReasoning || lastMsg.reasoning_content
                      }]
                    }
                  }
                  return {
                    ...prev,
                    [currentConvId]: [...msgs, { 
                      role: 'assistant', 
                      content: fullResponse,
                      reasoning_content: fullReasoning
                    }]
                  }
                })
              }
              
              if (parsed.done) {
                loadConversations()
              }
              
              if (parsed.summary_generating !== undefined) {
                console.log('收到 summary_generating:', parsed.summary_generating)
                setSummaryGeneratingMap(prev => ({ ...prev, [currentConvId]: parsed.summary_generating }))
              }
              
              if (parsed.done) {
                break
              }
            } catch (e) {
              console.error('解析响应失败:', e)
            }
          }
        }
      }
      
    } catch (err) {
      if (err.name === 'AbortError') {
      } else {
        setError(err.message || '发生错误，请稍后重试')
      }
    } finally {
      setLoadingMap(prev => ({ ...prev, [currentConvId]: false }))
      delete abortControllersRef.current[currentConvId]
    }
  }

  const handleStop = (convId) => {
    if (abortControllersRef.current[convId]) {
      abortControllersRef.current[convId].abort()
      delete abortControllersRef.current[convId]
      setLoadingMap(prev => ({ ...prev, [convId]: false }))
      setUserScrolledUp(false)
      logUserAction('stop_response')
    }
  }

  const toggleReasoning = (msgIdx) => {
    const key = `${conversationId}-${msgIdx}`
    setExpandedReasoning(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
    logUserAction('toggle_reasoning', { message_index: msgIdx })
  }

  const isConvLoading = (convId) => loadingMap[convId] || false

  return (
    <div className="chat-layout">
      <aside className={`chat-sidebar ${showSidebar ? 'open' : 'collapsed'}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={createNewConversation}>
            <PlusIcon />
            新建对话
          </button>
        </div>
        <div className="conversation-list">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`conversation-item ${conversationId === conv.id ? 'active' : ''}`}
              onClick={() => loadConversation(conv.id)}
            >
              <ChatIcon />
              <span className="conversation-title">{conv.title}</span>
              {isConvLoading(conv.id) && (
                <span className="loading-indicator" title="正在回复">⏳</span>
              )}
              <button 
                className="delete-btn"
                onClick={(e) => deleteConversation(conv.id, e)}
                title="删除对话"
              >
                <TrashIcon />
              </button>
            </div>
          ))}
        </div>
      </aside>

      <main className="chat-main">
        <div className="chat-header-bar">
          <button 
            className="toggle-sidebar-btn"
            onClick={() => setShowSidebar(!showSidebar)}
          >
            <MenuIcon />
          </button>
        </div>

        <div className="messages-container" ref={messagesContainerRef} onScroll={handleScroll}>
          {!conversationId ? (
            <div className="empty-state">
              <EmptyIcon />
              <h3>开始智能对话</h3>
              <p>基于大语言模型的智能对话系统</p>
              <p className="empty-hint">选择或创建一个对话开始交流</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="empty-state">
              <EmptyIcon />
              <h3>开始智能对话</h3>
              <p>基于大语言模型的智能对话系统</p>
              <p className="empty-hint">输入您的问题开始交流</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? <UserIcon /> : <BotIcon />}
                </div>
                <div className="message-content">
                  {msg.role === 'assistant' && msg.reasoning_content && (
                    <div className="reasoning-section">
                      <div 
                        className="reasoning-toggle"
                        onClick={() => toggleReasoning(idx)}
                      >
                        <span className="reasoning-icon">
                          <ThinkIcon />
                        </span>
                        <span className="reasoning-title">已思考</span>
                        <span className="reasoning-arrow">
                          {expandedReasoning[`${conversationId}-${idx}`] ? <ChevronUpIcon /> : <ChevronDownIcon />}
                        </span>
                      </div>
                      <div className="reasoning-content-box">
                        <div className="reasoning-content">{msg.reasoning_content}</div>
                      </div>
                    </div>
                  )}
                  <div className="message-text">
                    {msg.role === 'assistant' ? (
                      <MarkdownContent content={msg.content} />
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          {loading && messages[messages.length - 1]?.role !== 'assistant' && (
            <div className="message assistant loading">
              <div className="message-avatar">
                <BotIcon />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="chat-form">
          {summaryGenerating && (
            <div className="summary-generating-tip" style={{background: 'yellow', padding: '10px'}}>
              记忆正在生成中，请稍候...
            </div>
          )}
          <div className="input-row">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  if (prompt.trim() && !loading && !summaryGenerating) {
                    handleSubmit(e)
                  }
                }
              }}
              placeholder="请输入您的问题..."
              rows={1}
              disabled={loading || summaryGenerating || !conversationId}
              className="chat-input"
            />

            <div className="button-group">
              <button
                type="button"
                onClick={() => setThinkMode(!thinkMode)}
                className={`think-toggle-btn ${thinkMode ? 'active' : ''}`}
                title={thinkMode ? '思考模式已开启，点击关闭' : '点击开启思考模式'}
              >
                <span className="think-icon-wrapper">
                  <ThinkIcon />
                </span>
                <span className="think-label">{thinkMode ? 'DeepThink' : 'DeepThink'}</span>
              </button>
              {loading ? (
                <button
                  type="button"
                  onClick={() => handleStop(conversationId)}
                  className="submit-btn stop-btn"
                >
                  <span className="spinner"></span>
                  停止
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!prompt.trim() || !conversationId}
                  className="submit-btn"
                >
                  <SendIcon />
                </button>
              )}
            </div>
          </div>
        </form>

        {error && (
          <div className="error-message">
            <strong>错误：</strong>{error}
          </div>
        )}
      </main>
    </div>
  )
}

export default Chat
