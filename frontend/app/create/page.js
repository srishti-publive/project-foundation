"use client"

import { useState } from "react"
import { createTask } from "../../lib/api"
import "../globals.css"

export default function CreateTask() {
  const [name, setName] = useState("")
  const [tool, setTool] = useState("")
  const [user, setUser] = useState("")
  const [priority, setPriority] = useState("medium")
  const [scheduledAt, setScheduledAt] = useState("")

  async function handleSubmit(e) {
    e.preventDefault()

    await createTask({
      name,
      tool_name: tool,
      user_id: Number(user),
      priority,
      ...(scheduledAt ? { scheduled_at: scheduledAt } : {}),
    })

    alert("Task created")
  }

  return (
    <div className="wrapper">
      <div className="container">
        <h1 className="title">Create Task</h1>

        <form onSubmit={handleSubmit}>
          <input
            className="input"
            placeholder="Task Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <input
            className="input"
            placeholder="Tool Name"
            value={tool}
            onChange={(e) => setTool(e.target.value)}
          />

          <input
            className="input"
            placeholder="User ID"
            value={user}
            onChange={(e) => setUser(e.target.value)}
          />

          <label className="form-label">Priority</label>
          <select
            className="select"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>

          <label className="form-label">
            Scheduled At{" "}
            <span style={{ fontWeight: 400, textTransform: "none", color: "#b0a898" }}>
              (optional)
            </span>
          </label>
          <input
            type="datetime-local"
            className="input"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
          />

          <button className="button">Create Task</button>
        </form>
      </div>
    </div>
  )
}
