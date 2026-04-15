# Seed the database with sample tasks

Run this curl sequence to create 5 sample tasks:

curl -X POST http://localhost:8000/api/tasks/bulk-create/ \
  -H "Content-Type: application/json" \
  -d '[
    {"name":"Email Report","tool_name":"email_tool","user_id":1,"priority":"high"},
    {"name":"Generate PDF","tool_name":"pdf_tool","user_id":1,"priority":"medium"},
    {"name":"Sync CRM","tool_name":"crm_sync","user_id":2,"priority":"low"},
    {"name":"Send Alert","tool_name":"notify","user_id":1,"priority":"high"},
    {"name":"Archive Logs","tool_name":"archiver","user_id":3,"priority":"low"}
  ]'