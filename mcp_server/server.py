# mcp_server/server.py
from __future__ import annotations

import asyncio

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

API = "http://localhost:8000/api"
app = Server("publive-tasks")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_tasks",
            description="List all tasks, with an optional status filter.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed"],
                        "description": "Filter tasks by status.",
                    },
                },
            },
        ),
        Tool(
            name="create_task",
            description="Create a new task.",
            inputSchema={
                "type": "object",
                "required": ["name", "tool_name", "user_id"],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Human-readable task name.",
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Identifier for the tool that processes this task.",
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "ID of the user who owns the task.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Task priority (default: medium).",
                    },
                    "input_data": {
                        "type": "string",
                        "description": "Optional free-form input payload.",
                    },
                    "scheduled_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO-8601 scheduled run time.",
                    },
                },
            },
        ),
        Tool(
            name="next_task",
            description="Get the highest-priority pending task that is ready to run.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="update_status",
            description="Update a task's status.",
            inputSchema={
                "type": "object",
                "required": ["task_id", "status"],
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task to update.",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed"],
                        "description": "New status value.",
                    },
                },
            },
        ),
        Tool(
            name="claim_task",
            description=(
                "Atomically claim a pending task, transitioning it to running. "
                "Returns the updated task, or an error dict if the task is already "
                "claimed, completed, or missing."
            ),
            inputSchema={
                "type": "object",
                "required": ["task_id"],
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task to claim.",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        async with httpx.AsyncClient() as client:
            if name == "list_tasks":
                r = await client.get(f"{API}/tasks/", params=arguments)
                return r.json()

            elif name == "create_task":
                r = await client.post(f"{API}/tasks/create/", json=arguments)
                return r.json()

            elif name == "next_task":
                r = await client.get(f"{API}/tasks/next/")
                body = r.json()
                # The backend always returns 200; an empty queue is signalled
                # by body["task"] being null, not by a non-200 status code.
                if body.get("task") is None:
                    return {"detail": "No claimable tasks.", "task": None}
                return body

            elif name == "update_status":
                task_id = arguments.pop("task_id")
                r = await client.patch(
                    f"{API}/tasks/{task_id}/status/", json=arguments
                )
                return r.json()

            elif name == "claim_task":
                task_id = arguments["task_id"]
                r = await client.post(f"{API}/tasks/{task_id}/claim/")
                if r.status_code == 409:
                    return {"error": "already_claimed", "task_id": task_id}
                return r.json()

    except httpx.RequestError:
        # Django is down or unreachable — return a clean error instead of
        # letting an unhandled exception crash the MCP process.
        return {"error": "backend_unavailable"}


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
