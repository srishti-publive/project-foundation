// Configurable API base URL. Falls back to localhost for local dev.
// Set NEXT_PUBLIC_API_URL in your environment for other deployments.
const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

/**
 * Wrap a fetch call with consistent error handling. Non-2xx responses
 * throw an Error with the status code and, when available, the JSON
 * `detail` or `error` field from the backend.
 */
async function request(url, options = {}) {
  let res
  try {
    res = await fetch(url, options)
  } catch (networkErr) {
    throw new Error(`Network error contacting ${url}: ${networkErr.message}`)
  }

  // 204 No Content — nothing to parse.
  if (res.status === 204) {
    return null
  }

  let body = null
  try {
    body = await res.json()
  } catch {
    // Response was not JSON; leave body as null.
  }

  if (!res.ok) {
    const detail =
      (body && (body.detail || body.error)) || res.statusText || "Request failed"
    const err = new Error(`API ${res.status}: ${detail}`)
    err.status = res.status
    err.body = body
    throw err
  }

  return body
}

export async function getTasks(status = "") {
  const url = status
    ? `${API_URL}/tasks/?status=${encodeURIComponent(status)}`
    : `${API_URL}/tasks/`
  return request(url)
}

export async function createTask(task) {
  return request(`${API_URL}/tasks/create/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(task),
  })
}

export async function updateTaskStatus(id, status) {
  return request(`${API_URL}/tasks/${id}/status/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  })
}

export async function claimTask(id) {
  return request(`${API_URL}/tasks/${id}/claim/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
}

export async function getNextTask() {
  return request(`${API_URL}/tasks/next/`)
}

export async function getScheduledTasks() {
  return request(`${API_URL}/tasks/scheduled/`)
}
