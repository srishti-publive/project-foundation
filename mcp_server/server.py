# mcp_server/server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
import httpx, asyncio

API = "http://localhost:8000/api"
app = Server("publive-tasks")

@app.list_tools()
async def list_tools():
    return [
        {"name": "list_tasks",    "description": "List all tasks, optional status filter"},
        {"name": "create_task",   "description": "Create a new task"},
        {"name": "next_task",     "description": "Get next claimable task"},
        {"name": "update_status", "description": "Update a task's status"},
    ]

@app.call_tool()
async def call_tool(name, arguments):
    async with httpx.AsyncClient() as client:
        if name == "list_tasks":
            r = await client.get(f"{API}/tasks/", params=arguments)
            return r.json()
        elif name == "create_task":
            r = await client.post(f"{API}/tasks/create/", json=arguments)
            return r.json()
        elif name == "next_task":
            r = await client.get(f"{API}/tasks/next/")
            return r.json() if r.status_code == 200 else {"detail": "No tasks"}
        elif name == "update_status":
            task_id = arguments.pop("task_id")
            r = await client.patch(f"{API}/tasks/{task_id}/status/", json=arguments)
            return r.json()

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())