import { useState } from 'react'
import AgentList from './AgentList'
import AgentDetail from './AgentDetail'

function MeetingRoom() {
  const [selectedAgent, setSelectedAgent] = useState(null)

  const handleSelectAgent = (agent) => {
    setSelectedAgent(agent)
  }

  const handleBack = () => {
    setSelectedAgent(null)
  }

  if (selectedAgent) {
    return <AgentDetail agent={selectedAgent} onBack={handleBack} />
  }

  return (
    <div className="content-wrapper fade-in">
      <div className="content-card">
        <AgentList onSelectAgent={handleSelectAgent} />
      </div>
    </div>
  )
}

export default MeetingRoom