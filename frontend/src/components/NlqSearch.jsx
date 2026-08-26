import { useState } from 'react'
import { askQuestion } from '../api/nlq'
import { getErrorMessage } from '../api/errors'
import NlqSearchBar from './NlqSearchBar'
import NlqResultPanel from './NlqResultPanel'

export default function NlqSearch() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [networkError, setNetworkError] = useState('')

  async function handleAsk(question) {
    setLoading(true)
    setNetworkError('')
    setResult(null)
    try {
      const data = await askQuestion(question)
      setResult(data)
    } catch (err) {
      setNetworkError(getErrorMessage(err, 'Could not reach the server. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="nlq-search-section">
      <h2 className="nlq-search-heading">Ask anything about your business</h2>
      <NlqSearchBar onAsk={handleAsk} loading={loading} />
      {loading && (
        <p className="nlq-thinking">
          <span className="nlq-thinking-dots">
            <span />
            <span />
            <span />
          </span>
          Thinking…
        </p>
      )}
      {networkError && <p className="error-text">{networkError}</p>}
      {!loading && result && <NlqResultPanel result={result} />}
    </div>
  )
}
