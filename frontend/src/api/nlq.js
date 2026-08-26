import apiClient from './axios'

export function askQuestion(question) {
  return apiClient.post('/nlq/ask', { question }).then((res) => res.data)
}
