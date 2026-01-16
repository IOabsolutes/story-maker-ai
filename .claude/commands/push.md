---
allowed-tools: Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(git status:*), Bash(git diff:*)
description: Stage all changes, commit with summary + bullets, and push
---

Analyze the current changes and create a commit:

1. First run `git status` and `git diff` to understand what changed
2. Run `git add .` to stage all changes
3. Create a descriptive commit message with:
   - First line: short summary (max 50 chars, imperative mood)
   - Empty line
   - Bullet points describing each significant change
4. Run `git commit -m "message"`
5. Run `git push`

Commit message format:
```
Short summary of changes

- Change 1 description
- Change 2 description
- Change 3 description
```
