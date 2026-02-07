import Chat from './components/Chat'
import './index.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>🤖 LLM Chat</h1>
        <p>基于 DeepSeek 大语言模型的智能对话</p>
      </header>
      <main className="app-main">
        <Chat />
      </main>
      <footer className="app-footer">
        <p>Powered by DeepSeek API</p>
      </footer>
    </div>
  )
}

export default App