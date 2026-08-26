import apiClient from './axios'

export function listProducts(params = {}) {
  return apiClient.get('/products', { params }).then((res) => res.data)
}

export function getProduct(id) {
  return apiClient.get(`/products/${id}`).then((res) => res.data)
}

export function createProduct(data) {
  return apiClient.post('/products', data).then((res) => res.data)
}

export function updateProduct(id, data) {
  return apiClient.put(`/products/${id}`, data).then((res) => res.data)
}

export function deleteProduct(id) {
  return apiClient.delete(`/products/${id}`)
}
