const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const configApi = {
  getProviders: async () => {
    const response = await fetch(`${API_URL}/config/providers`)
    if (!response.ok) throw new Error('Failed to fetch providers')
    return response.json()
  },

  getActiveProviders: async () => {
    const response = await fetch(`${API_URL}/config/providers/active`)
    if (!response.ok) throw new Error('Failed to fetch active providers')
    return response.json()
  },

  addProvider: async (provider) => {
    const response = await fetch(`${API_URL}/config/providers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(provider)
    })
    if (!response.ok) throw new Error('Failed to add provider')
    return response.json()
  },

  updateProvider: async (name, provider) => {
    const response = await fetch(`${API_URL}/config/providers/${name}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(provider)
    })
    if (!response.ok) throw new Error('Failed to update provider')
    return response.json()
  },

  deleteProvider: async (name) => {
    const response = await fetch(`${API_URL}/config/providers/${name}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete provider')
    return response.json()
  },

  toggleProvider: async (name) => {
    const response = await fetch(`${API_URL}/config/providers/${name}/toggle`, {
      method: 'PATCH'
    })
    if (!response.ok) throw new Error('Failed to toggle provider')
    return response.json()
  },

  initPresetProviders: async () => {
    const response = await fetch(`${API_URL}/config/providers/init-presets`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to init preset providers')
    return response.json()
  },

  getModels: async () => {
    const response = await fetch(`${API_URL}/config/models`)
    if (!response.ok) throw new Error('Failed to fetch models')
    return response.json()
  },

  getEnabledModels: async () => {
    const response = await fetch(`${API_URL}/config/models/enabled`)
    if (!response.ok) throw new Error('Failed to fetch enabled models')
    return response.json()
  },

  getDefaultModel: async () => {
    const response = await fetch(`${API_URL}/config/models/default`)
    if (!response.ok) throw new Error('Failed to fetch default model')
    return response.json()
  },

  addOrUpdateModel: async (model) => {
    const response = await fetch(`${API_URL}/config/models`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(model)
    })
    if (!response.ok) throw new Error('Failed to add/update model')
    return response.json()
  },

  deleteModel: async (provider, modelName) => {
    const response = await fetch(`${API_URL}/config/models/${provider}/${modelName}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete model')
    return response.json()
  },

  setDefaultModel: async (configId) => {
    const response = await fetch(`${API_URL}/config/models/${configId}/set-default`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to set default model')
    return response.json()
  },

  toggleModel: async (configId) => {
    const response = await fetch(`${API_URL}/config/models/${configId}/toggle`, {
      method: 'PATCH'
    })
    if (!response.ok) throw new Error('Failed to toggle model')
    return response.json()
  },

  getModelCatalog: async () => {
    const response = await fetch(`${API_URL}/config/model-catalog`)
    if (!response.ok) throw new Error('Failed to fetch model catalog')
    return response.json()
  },

  getProviderModelCatalog: async (provider) => {
    const response = await fetch(`${API_URL}/config/model-catalog/${provider}`)
    if (!response.ok) throw new Error('Failed to fetch provider model catalog')
    return response.json()
  },

  saveModelCatalog: async (catalog) => {
    const response = await fetch(`${API_URL}/config/model-catalog`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(catalog)
    })
    if (!response.ok) throw new Error('Failed to save model catalog')
    return response.json()
  },

  deleteModelCatalog: async (provider) => {
    const response = await fetch(`${API_URL}/config/model-catalog/${provider}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete model catalog')
    return response.json()
  },

  initModelCatalog: async () => {
    const response = await fetch(`${API_URL}/config/model-catalog/init`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to init model catalog')
    return response.json()
  }
}

export default configApi
