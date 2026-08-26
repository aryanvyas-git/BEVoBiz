import apiClient from './axios'

export function listSales(params = {}) {
  return apiClient.get('/sales', { params }).then((res) => res.data)
}

export function createSale(data) {
  return apiClient.post('/sales', data).then((res) => res.data)
}
