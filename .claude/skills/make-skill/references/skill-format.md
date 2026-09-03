# Skill file format reference

A skill is a directory with a `SKILL.md` and optional support files.

```
.claude/skills/<name>/
├── SKILL.md          required: frontmatter + instructions
├── scripts/          optional: code Claude runs (no context cost until executed)
├── references/       optional: docs Claude reads only when needed
├── assets/           optional: templates, images, fonts used in output
└── evals/evals.json  optional: test prompts used by /make-skill
```

## Frontmatter fields

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Kebab-case identifier. Must match the directory name. Becomes `/<name>`. |
| `description` | string | What it does and when to use it. This is the only text Claude sees before deciding to load the skill. Max 1024 characters. |
| `argument-hint` | string | Placeholder shown in the slash menu, e.g. `[file] [style]`. |
| `disable-model-invocation` | bool | `true` means only an explicit `/<name>` runs it; Claude will not pick it up on its own. Use for side-effecting workflows. |
| `user-invocable` | bool | `false` hides it from the `/` menu; only Claude can load it in the background. |
| `allowed-tools` | list/string | Tools the skill may use without a permission prompt while it runs. |
| `model` | string | Model override for the skill's run. |
| `context` | `fork` | Run the skill in a forked subagent context instead of the main conversation. |
| `agent` | string | With `context: fork`, which agent type to use. |
| `hooks` | map | Hooks scoped to this skill's lifetime. |
| `paths` | list | Glob patterns; the skill is only offered when the user is working in matching files. |

Only `name` and `description` are required.

## Substitutions in the body

| Token | Expands to |
|---|---|
| `$ARGUMENTS` | Everything the user typed after `/<name>`. |
| `$ARGUMENTS[0]`, `$ARGUMENTS[1]` (also `$0`, `$1`) | Individual space-separated arguments. |
| `${CLAUDE_SESSION_ID}` | The current session id. |
| `${CLAUDE_SKILL_DIR}` | Absolute path of the skill directory, useful for locating bundled scripts. |
| `` !`command` `` | Runs the shell command when the skill loads and inlines its output. Good for injecting `git status` or a file listing. |

## Where skills live and who wins

| Location | Scope |
|---|---|
| `.claude/skills/<name>/` | This repository. Committed, shared with everyone who clones it. |
| `~/.claude/skills/<name>/` | Your user account, every repo. |
| Plugins | Namespaced as `plugin:name`. |

When two skills share a name, the project one takes precedence over the user one.

## Progressive disclosure

Three levels are loaded at different times, so put content where it costs least:

1. `name` + `description`: always in context. Keep it tight.
2. `SKILL.md` body: loaded when the skill triggers. Aim for well under 500 lines.
3. `scripts/`, `references/`, `assets/`: loaded or run only when the body says to.
