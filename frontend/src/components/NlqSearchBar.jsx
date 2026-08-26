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
      <input
        type="text"
        className="nlq-search-input"
        placeholder={PLACEHOLDER}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={loading}
      />
      <button type="submit" disabled={loading || !question.trim()}>
        {loading ? 'Thinking…' : 'Ask'}
      </button>
    </form>
  )
}
