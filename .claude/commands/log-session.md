---
description: Summarise the current session and append it to docs/ai_edit_log.md
allowed-tools: Bash(date:*), Read, Edit
---

Summarise the current conversation session and append the summary to `docs/ai_edit_log.md`.

Append a new entry (do not overwrite existing content) using exactly this template:

```
## Session: <current timestamp> (id: <session id>)

**Context:** What were you trying to accomplish?

**AI Tool Used:** Claude

**Prompt/Request:** What exactly did you ask the AI?

**AI Response:** Summary of what the AI generated (don't copy entire code blocks)
```

Guidelines:
- Get the timestamp with `date '+%Y-%m-%d %H:%M:%S'`.
- Get the session id from the `CLAUDE_CODE_SESSION_ID` environment variable (e.g. `printenv CLAUDE_CODE_SESSION_ID`).
- End each `**...**` section line with two trailing spaces so Markdown renders each on its own line.
- **AI Tool Used** is always Claude.
- **Context:** describe the overall goal of the session in one or two sentences.
- **Prompt/Request:** summarise what the user actually asked for across the session, not verbatim.
- **AI Response:** summarise what was built or changed. Reference files by name. Do not paste full code blocks.
- Please add an empty line between each section.
- If `docs/ai_edit_log.md` is empty, this is the first entry; otherwise append below the existing entries.
