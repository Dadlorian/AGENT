# AGENT

A home for reusable Claude Code skills. Anything committed under `.claude/skills/` is available in every Claude Code session on this repo, both as a `/slash-command` and as something Claude reaches for on its own when a request matches the skill's description.

## Using a skill

Type `/` in Claude Code to see the menu, or ask in plain words. To see what is here:

```
/list-skills
```

## Making a new skill

Describe what you want and let Claude build it:

```
/make-skill a skill that drafts release notes from the commits since the last tag
```

That runs the `make-skill` workflow: pin down what the skill does and when it should trigger, scaffold `.claude/skills/<name>/`, write the instructions, validate the result, add a couple of test prompts, and try it once. You can also point it at an existing skill to improve it:

```
/make-skill tighten up list-skills, it is too chatty
```

## Layout

```
.claude/skills/
├── make-skill/           create or improve skills
│   ├── SKILL.md
│   ├── scripts/scaffold_skill.py    creates the directory + template
│   ├── scripts/validate_skill.py    checks frontmatter, paths, evals
│   └── references/skill-format.md   frontmatter fields, substitutions, precedence
└── list-skills/          inventory of what is here
    ├── SKILL.md
    └── scripts/list_skills.py
```

Each skill folder holds a `SKILL.md` (required) plus optional `scripts/`, `references/`, `assets/`, and `evals/evals.json` with test prompts.

## Checking everything is well-formed

```bash
python3 .claude/skills/make-skill/scripts/validate_skill.py --all
```
