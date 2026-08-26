// FastAPI returns `detail` as a plain string for most errors, but as an
// array of Pydantic validation-error objects for 422s. Rendering that
// array directly as a JSX child crashes ("Objects are not valid as a
// React child"), so every place that shows an API error message must go
// through this instead of reading err.response.data.detail directly.
export function getErrorMessage(err, fallback) {
  const detail = err?.response?.data?.detail

  if (typeof detail === 'string' && detail) {
    return detail
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg || String(d)).join('; ')
  }

  return fallback
}
