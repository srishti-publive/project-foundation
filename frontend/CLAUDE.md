# Frontend CLAUDE.md

@AGENTS.md

- Next.js 16 App Router. All pages are client components ('use client').
- API base: http://localhost:8000/api — all calls go through lib/api.js.
- Routes: /tasks (list), /create (form), / (stock Next landing).
- Styling: globals.css for .card, .status — Tailwind for layout.
- DO NOT add direct fetch() calls in page components — use lib/api.js.