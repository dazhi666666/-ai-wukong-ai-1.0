const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export function useUserActionLog() {
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

  return { logUserAction }
}

export function withUserActionLog(WrappedComponent, actionName) {
  return function WithUserActionLog(props) {
    const { logUserAction } = useUserActionLog()
    
    return (
      <WrappedComponent
        {...props}
        logUserAction={logUserAction}
        actionName={actionName}
      />
    )
  }
}
