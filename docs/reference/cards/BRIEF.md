# Brief: writing a reference-model card profile

You are defining one or two cards of an agentic-platform reference model, in a repo whose
central rule is that **nothing may be asserted**. Read this whole file before starting.

## The rule

Every claim-bearing field is one of exactly two things:

- **`origin: "sourced"`** — cites real record ids, and carries a `quote` that appears
  **byte-for-byte** in the *source text* of one of them.
- **`origin: "proposed"`** — this repo's own reasoning, and its `text` says so.

There is no third option. A field with no evidence is `proposed`, not asserted.

**Source text means `snippet` or `read` on a research record — never `claim`.** A record's
`claim` field is this repo's prose *about* a source. A quote matching it is the repo citing
itself, which reads as evidence and is not. That exact hole was found in another checker
where 18 of 946 citations relied on it. `tools/validate_card_profiles.py` is written so it
cannot open here. For non-research records (`F-`, `T-`, `REF-`, `E-`, `A-`) the `text` field
is the source text.

Citing a `T-` record (the owner's TARGET.md) is legitimate and often the right answer for a
definition — but say so in the text, e.g. "this repo's own target architecture states…".
An owner declaration is evidence of intent, not evidence of industry practice. Do not blur them.

## Read first

- `schemas/card-profile.schema.json` — the shape to produce
- `tools/validate_card_profiles.py` — the gate; read it so you know exactly what passes
- `docs/reference/reference-model.json` — all 40 cards: address, name, status, standard badge
- `docs/reference/cards/3-3.json` — a worked example that passes. Match its rigour.

## Finding evidence

Search before researching. Do not re-research what exists:

```
python3 tools/kb_index.py search "<terms>"     # 2420 citable records, indexed
python3 tools/kb.py show <id>                  # read any F-/T-/X-/E-/A-/REF- record
```

If nothing covers your card, write new research records into
`kb/research/refmodel-<address-with-dashes>-<slug>.jsonl` against
`schemas/research.schema.json`, following
`.claude/skills/build-skill-authoring/references/build-research-record.md`.

**Capture pages with `python3 tools/capture.py <url>`, never with WebFetch.** WebFetch
returns a language model's rendering of a page; 30 records written from it had snippets that
were not in the source, including one with invented statistics. `capture.py` walks a ladder
(api → markdown → service → html) and returns the publisher's own text. Set `fetch_tool` to
the rung that succeeded. A snippet must be copied byte-for-byte from what capture returns —
do not tidy punctuation, do not join two fragments across an ellipsis.

If a fetch is refused, record `status: "blocked"` and say so. A blocked record is honest.

## Filling the fields

| Field | What it is |
|---|---|
| `definition` | What the element **is**, in one or two sentences. |
| `standards` | Only standards with a directory under `standards/`. `role` = what it governs; `covers` = what it does **not**, where that matters. |
| `tools` | Real named implementations. `in_use_here: true` **only** if this repo actually uses it — check, don't assume. |
| `landscape` | How the options genuinely differ and the real tradeoff. A `proposed` synthesis is often the honest answer here. |
| `usage` | The shape of the call. Not a tutorial. |
| `gaps` | What is missing or unsettled. **An empty `gaps` list fails the gate**, and rightly — a card with nothing missing is a claim in itself. |

## A card marked `built` deserves suspicion

Most cards you will be given are marked `built`, meaning this platform claims the element
exists and works — with nothing currently backing that. If the evidence does not support the
claim, **say so in `gaps`**. Finding that a `built` card is unevidenced is a valuable result,
not a failed task. Do not manufacture support for it.

Equally, if defining a card reveals it overlaps another card, or that its boundary is our
bucketing rather than a real seam, put that in `gaps`. That is how the model gets better.

## Done means

```
python3 tools/validate_card_profiles.py     # 0 errors
python3 tools/verify_snippets.py --check    # only if you wrote new research records
```

Iterate until clean. **Do not weaken the checker to pass** — if you think the checker is
wrong, say so in your report instead of editing it. Do not commit. Do not edit `schemas/`,
the checkers, or another card's profile.
