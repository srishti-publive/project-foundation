# Add a New Feature (Full Stack)

When adding a feature end-to-end:
1. Start with backend: model → migration → serializer → view → url
2. Verify with curl before touching frontend
3. Add to frontend/lib/api.js
4. Add UI in app/ (new route or update existing)
5. Update CLAUDE.md if architecture changes
6. Update .claude/context/ files