---
name: list-skills
description: Show every skill available in this repository with how to invoke each one. Use when the user asks what skills or slash commands exist here, what Claude can do in this repo, "what commands do I have", or wants a quick inventory before creating a new skill with /make-skill.
---

# List Skills

Give the user a one-screen inventory of the skills committed to this repo, so they know what is already available before asking for something new.

## Steps

1. Run the bundled script from anywhere inside the repo:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/list_skills.py
   ```

   It reads the frontmatter of every `.claude/skills/*/SKILL.md` and prints one line per skill: how to invoke it, whether Claude can trigger it automatically or only via `/name`, and its description. Add `--json` if you need structured output.

2. Show the result as a short table with three columns: invoke, mode, what it does. Keep descriptions to one line each; the reader is scanning, not studying.

3. If the user seems to be looking for something that is not there, mention that `/make-skill <description>` creates one.

## Output

```
| Invoke              | Mode   | What it does                              |
|---------------------|--------|-------------------------------------------|
| /list-skills        | auto   | Inventory of skills in this repo          |
| /make-skill <idea>  | auto   | Create or improve a skill                 |
```
