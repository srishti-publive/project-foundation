# Database Schema

## Table: api_task
| Field       | Type         | Notes              |
|-------------|-------------|-------------------|
| task_id     | AutoField    | Primary key        |
| name        | CharField    | max 200            |
| tool_name   | CharField    | max 200            |
| user_id     | IntegerField | not a FK           |
| input_data  | TextField    | nullable           |
| output_data | TextField    | nullable           |
| status      | CharField    | default: pending   |
| created_at  | DateTimeField| auto_now_add       |

## Task Object
{
  task_id: int,
  name: string,
  tool_name: string,
  user_id: int,
  input_data: string|null,
  output_data: string|null,
  status: pending|running|completed|failed,
  created_at: datetime
}