"use client"

import { useEffect, useState } from "react"
import { getTasks, updateTaskStatus } from "../../lib/api"
import "../globals.css"

const PRIORITY_RANK = { high: 1, medium: 2, low: 3 }

export default function TasksPage() {
  const [tasks, setTasks] = useState([])
  const [statusFilter, setStatusFilter] = useState("")
  const [priorityFilter, setPriorityFilter] = useState("")
  const [sortBy, setSortBy] = useState("priority")

  async function loadTasks(status = "") {
    setStatusFilter(status)
    const data = await getTasks(status)
    setTasks(data)
  }

  useEffect(() => {
    loadTasks()
  }, [])

  async function changeStatus(id, status) {
    await updateTaskStatus(id, status)
    loadTasks(statusFilter)
  }

  const displayedTasks = tasks
    .filter((t) => !priorityFilter || t.priority === priorityFilter)
    .sort((a, b) => {
      if (sortBy === "priority") {
        return (PRIORITY_RANK[a.priority] ?? 2) - (PRIORITY_RANK[b.priority] ?? 2)
      }
      return new Date(a.created_at) - new Date(b.created_at)
    })

  return (
    <div className="wrapper">
      <div className="container">
        <h1 className="title">Task List</h1>

        <div className="filter-group">
          <div className="filters">
            <span className="filter-label">Status</span>
            <button
              className={statusFilter === "" ? "active" : ""}
              onClick={() => loadTasks("")}
            >
              All
            </button>
            <button
              className={statusFilter === "running" ? "active" : ""}
              onClick={() => loadTasks("running")}
            >
              Running
            </button>
            <button
              className={statusFilter === "completed" ? "active" : ""}
              onClick={() => loadTasks("completed")}
            >
              Completed
            </button>
            <button
              className={statusFilter === "failed" ? "active" : ""}
              onClick={() => loadTasks("failed")}
            >
              Failed
            </button>
          </div>

          <div className="filters">
            <span className="filter-label">Priority</span>
            <button
              className={priorityFilter === "" ? "active" : ""}
              onClick={() => setPriorityFilter("")}
            >
              All
            </button>
            <button
              className={priorityFilter === "high" ? "active" : ""}
              onClick={() => setPriorityFilter("high")}
            >
              High
            </button>
            <button
              className={priorityFilter === "medium" ? "active" : ""}
              onClick={() => setPriorityFilter("medium")}
            >
              Medium
            </button>
            <button
              className={priorityFilter === "low" ? "active" : ""}
              onClick={() => setPriorityFilter("low")}
            >
              Low
            </button>
          </div>

          <div className="filters">
            <span className="filter-label">Sort by</span>
            <button
              className={sortBy === "priority" ? "active" : ""}
              onClick={() => setSortBy("priority")}
            >
              Priority
            </button>
            <button
              className={sortBy === "created_at" ? "active" : ""}
              onClick={() => setSortBy("created_at")}
            >
              Date
            </button>
          </div>
        </div>

        {displayedTasks.length === 0 && <p>No tasks available</p>}

        {displayedTasks.map((task) => (
          <div key={task.task_id} className="card">
            <div className="card-header">
              <span className="card-title">{task.name}</span>
              <span className={`priority ${task.priority}`}>{task.priority}</span>
            </div>

            <p><b>Tool:</b> {task.tool_name}</p>
            <p><b>User:</b> {task.user_id}</p>

            <p className={`status ${task.status}`}>
              Status: {task.status}
            </p>

            <button onClick={() => changeStatus(task.task_id, "running")}>
              Start
            </button>

            <button onClick={() => changeStatus(task.task_id, "completed")}>
              Complete
            </button>

            <button onClick={() => changeStatus(task.task_id, "failed")}>
              Fail
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
