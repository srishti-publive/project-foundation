const API_URL = "http://localhost:8000/api"

export async function getTasks() {
  const res = await fetch(`${API_URL}/tasks/`)
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
