import apiClient from './axios'

export function getDashboardStats() {
  return apiClient.get('/dashboard/stats').then((res) => res.data)
}
