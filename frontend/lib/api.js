const API_URL = "http://localhost:8000/api"

export async function getTasks(status="") {
  const url = status
    ? `${API_URL}/tasks/?status=${status}`
    : `${API_URL}/tasks/`
    
  const res = await fetch(url)
  return res.json()
}

export async function createTask(task) {
  const res = await fetch(`${API_URL}/tasks/create/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(task)
  })

  return res.json()
}

export async function updateTaskStatus(id, status) {
  const res = await fetch(`${API_URL}/tasks/${id}/status/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ status })
  })

  return res.json()
}
