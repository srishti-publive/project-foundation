import { getTasks } from "../../lib/api"
import "../globals.css"

export default async function TasksPage() {
  const tasks = await getTasks()

  return (
    <div className="wrapper">
      <div className="container">
        <h1 className="title">Task List</h1>

        {tasks.length === 0 && <p>No tasks available</p>}

        {tasks.map((task) => (
          <div key={task.task_id} className="card">
            <p><b>Task:</b> {task.name}</p>
            <p><b>Tool:</b> {task.tool_name}</p>
            <p><b>User:</b> {task.user_id}</p>
          </div>
        ))}
      </div>
    </div>
  )
}