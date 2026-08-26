import { useState } from 'react'

const PLACEHOLDER =
  'Ask a question… e.g. "How many items did I sell yesterday?" or "What\'s my total profit this month?"'

export default function NlqSearchBar({ onAsk, loading }) {
  const [question, setQuestion] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || loading) return
    onAsk(trimmed)
  }

  return (
    <form className="nlq-search-form" onSubmit={handleSubmit}>
      <div className="nlq-search-input-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          className="nlq-search-input"
          placeholder={PLACEHOLDER}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
        />
      </div>
      <button type="submit" disabled={loading || !question.trim()}>
        {loading ? 'Thinking…' : 'Ask'}
      </button>
    </form>
  )
}
