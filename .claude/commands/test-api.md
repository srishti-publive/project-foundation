Test all API endpoints:
```bash
curl http://localhost:8000/api/tasks/
curl -X POST http://localhost:8000/api/tasks/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","tool_name":"test_tool","user_id":1}'
```