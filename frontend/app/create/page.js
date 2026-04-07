"use client"

import { useState } from "react"
import { createTask } from "../../lib/api"
import "../globals.css"

export default function CreateTask() {
  const [name, setName] = useState("")
  const [tool, setTool] = useState("")
  const [user, setUser] = useState("")

  async function handleSubmit(e) {
    e.preventDefault()

    await createTask({
      name,
      tool_name: tool,
      user_id: Number(user),
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

          <button className="button">Create Task</button>
        </form>
      </div>
    </div>
  )
}