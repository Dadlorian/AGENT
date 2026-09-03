---
name: make-skill
description: Create a new project skill in .claude/skills/ from a short description, or improve an existing one. Use this whenever the user says they want a skill, a slash command, a reusable workflow, a "recipe", to "teach Claude to do X every time", or to turn something just done in the conversation into a repeatable /command. Also use it when they ask to review, tighten, or test a skill that already exists in this repo.
argument-hint: <what the skill should do, or the name of an existing skill>
---

# Make Skill

Turn an idea into a working, validated skill under `.claude/skills/<name>/` so it is available in every session on this repo as `/<name>` and as something Claude picks up on its own when the description matches.

`$ARGUMENTS` is the user's request. It is usually a loose description ("a skill that writes release notes from git log") and sometimes the name of an existing skill to improve.

## 1. Pin down the intent

Before writing anything, make sure these four things are settled. Pull answers from the conversation first; if something is genuinely unclear and the answer would change the design, ask once, in one message, with all the questions together.

1. **What it does.** One sentence, outcome-focused.
2. **When it triggers.** The phrases and situations a user would actually say. This becomes the description, so collect concrete wording.
3. **What it produces.** A file, a message, a diff, a table. Be exact so runs are consistent.
4. **Inputs.** Does it take arguments via `/<name> <args>`? Files from the repo? Nothing?

If the user wants to capture something that just happened in the conversation, extract the steps, tools, and corrections from the transcript and confirm them back before proceeding.

## 2. Scaffold

Pick a kebab-case name that reads naturally after a slash (`/release-notes`, not `/rn`). Then:

```bash
python3 .claude/skills/make-skill/scripts/scaffold_skill.py <name> \
  --description "<draft description>" \
  [--argument-hint "<hint>"] [--with-scripts] [--with-references] [--user-only]
```

Use `--with-scripts` when a step is deterministic and repetitive (parsing, transforming files, calling an API). Code beats prose for that: it runs the same way every time and costs no context. Use `--with-references` when the skill needs domain detail that would bloat SKILL.md past a few hundred lines. Use `--user-only` for skills that should run only when typed as `/<name>`, never auto-triggered (deploys, anything with side effects the user wants to control).

## 3. Write the SKILL.md

Replace every template comment. Read `references/skill-format.md` if you need the frontmatter fields or substitution syntax.

Writing guidance that matters more than it looks:

- **The description does the triggering.** Claude tends to under-use skills, so make the description slightly pushy: name the task, then list the phrasings and adjacent situations that should pull it in, including cases where the user does not say the obvious keyword. Keep it under 1024 characters. All "when to use" content belongs here, not in the body.
- **Explain why, not just what.** Skills are read by a capable model. "Run the tests before committing, because a red push costs the reviewer a cycle" produces better judgment in unforeseen cases than "ALWAYS RUN TESTS". If you find yourself writing all-caps MUST or NEVER, rewrite it as a reason.
- **Prefer imperative steps** ("Read the changelog", "Run the bundled script") and show the expected output shape with a short example.
- **Keep the body lean.** Under 500 lines. Move reference material into `references/` and point to it with a sentence saying when to read it.
- **Generalize.** The skill will run on prompts you have not seen. Avoid instructions that only work for the example the user gave.

## 4. Validate

```bash
python3 .claude/skills/make-skill/scripts/validate_skill.py .claude/skills/<name>
```

Fix every error and read each warning. Warnings about leftover template comments or empty evals mean the skill is not finished yet.

## 5. Write test prompts

Put 2 or 3 realistic prompts into `evals/evals.json`, the kind a real user would type, with a sentence describing what a good result looks like. Show them to the user. These are what future iterations get measured against, and they are also the cheapest way to notice the description is too narrow.

If the outputs are objectively checkable (files produced, fields extracted, a fixed sequence of steps), add short verifiable `expectations`. If the output is a matter of taste (writing style, design), skip expectations and rely on the user's eye.

## 6. Try it

Run the first eval prompt against the new skill: read the SKILL.md and follow it as a fresh user would, or, when subagents are available, hand the prompt to one with the skill path. Compare what came out against the expected output. Fix the skill, not the test, when they disagree.

## 7. Hand it back

Tell the user, in a few lines:

- the skill name and how to invoke it (`/<name> <args>`)
- what it produces
- the test prompts you wrote and whether the trial run matched
- any judgment call you made that they might want to change

Commit the new directory if the user works from git in this repo.

## Improving an existing skill

When `$ARGUMENTS` names a skill that already exists, or the user is unhappy with one:

1. Read its SKILL.md and evals, and any transcript or output the user is reacting to.
2. Generalize from the complaint. One bad output usually points at a missing reason or a too-narrow instruction, not at a need for another rule.
3. Cut what is not pulling its weight. If the skill makes Claude do busywork, delete that part.
4. If several runs all wrote the same helper code, bundle it as a script.
5. Re-validate, re-run the evals, and summarize the before and after for the user.
