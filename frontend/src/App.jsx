import { useState } from 'react'
import Sidebar from './components/Sidebar'
import TopNav from './components/TopNav'
import Chat from './components/Chat'
import ModelConfig from './components/ModelConfig'
import Canvas from './components/workflow/Canvas'
import Logs from './components/Logs'
import DatabaseManager from './components/DatabaseManager'
import './index.css'

function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [isDarkMode, setIsDarkMode] = useState(false)

  const handleTabChange = (tab) => {
    setActiveTab(tab)
  }

  const handleThemeToggle = () => {
    setIsDarkMode(!isDarkMode)
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <div className="content-wrapper fade-in">
            <div className="content-card chat-page-card">
              <Chat />
            </div>
          </div>
        )
      case 'workflow':
        return (
          <div className="content-wrapper workflow-wrapper fade-in">
            <div className="page-header">
              <h1>工作流编排</h1>
              <p>可视化节点编排与执行</p>
            </div>
            <div className="workflow-canvas-container">
              <Canvas />
            </div>
          </div>
        )
      case 'model':
        return <ModelConfig />
      case 'logs':
        return (
          <div className="content-wrapper fade-in">
            <Logs />
          </div>
        )
      case 'database':
        return <DatabaseManager />
      default:
        return null
    }
  }

  return (
    <div className={`app ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
      <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />
      
      <div className="main-container">
        <TopNav 
          activeTab={activeTab} 
          isDarkMode={isDarkMode}
          onThemeToggle={handleThemeToggle}
        />
        
        <main className="main-content">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}

function WorkflowIcon() {
  return (
    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="14" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/>
      <path d="M10 7h4M10 17h4M7 10v4M17 10v4"/>
    </svg>
  )
}

export default App
