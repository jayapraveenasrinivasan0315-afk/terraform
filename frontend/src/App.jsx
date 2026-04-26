import React, { useState, useEffect } from 'react'

// In production (GCS static), this env var is replaced at build time
// Set VITE_API_URL to your Cloud Run service URL during `vite build`
const API = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [name, setName]     = useState('')
  const [names, setNames]   = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')
  const [success, setSuccess] = useState('')

  // Fetch all names on load
  useEffect(() => { fetchNames() }, [])

  async function fetchNames() {
    try {
      const res = await fetch(`${API}/api/names`)
      const data = await res.json()
      setNames(data)
    } catch {
      setError('Failed to load names')
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const res = await fetch(`${API}/api/names`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      if (!res.ok) throw new Error('Failed to save')
      const saved = await res.json()
      setNames(prev => [saved, ...prev])   // Add to top of list
      setName('')
      setSuccess(`"${saved.name}" saved!`)
    } catch {
      setError('Failed to save name. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="card">
        <h1>Names Store</h1>
        <p className="subtitle">Type a name → POST to FastAPI → Saved in PostgreSQL</p>

        <form onSubmit={handleSubmit} className="form">
          <input
            type="text"
            placeholder="Enter a name..."
            value={name}
            onChange={e => setName(e.target.value)}
            disabled={loading}
            autoFocus
          />
          <button type="submit" disabled={loading || !name.trim()}>
            {loading ? 'Saving...' : 'Save'}
          </button>
        </form>

        {error   && <p className="msg error">{error}</p>}
        {success && <p className="msg success">{success}</p>}

        <div className="list">
          <h2>Saved Names ({names.length})</h2>
          {names.length === 0
            ? <p className="empty">No names yet. Add one above!</p>
            : names.map(n => (
              <div key={n.id} className="item">
                <span className="item-name">{n.name}</span>
                <span className="item-time">
                  {new Date(n.created_at).toLocaleString()}
                </span>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  )
}
