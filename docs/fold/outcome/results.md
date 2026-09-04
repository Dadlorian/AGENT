# Outcome eval: does a folded skill improve the work?

At 19e61e4. One fresh Sonnet agent per cell; the with cell loaded the named skill first, the without cell was told to load none and not to read the skills folder. Graded by the mechanical checker named in tasks.json.

| Task | Skill | With skill | Without skill | What the without run missed |
|---|---|---|---|---|
| errors | `cap-errors` | 9 of 9 | 8 of 9 | correlation or run id present |
| intake | `cap-work-intake` | 15 of 15 | 15 of 15 | - |
| dod | `build-evidence` | 5 of 5 | 5 of 5 | - |

## Caveats

- The mechanical graders sat in the tree where both agents could read them; the without-skill intake agent reports it verified against check_intake.py, so that cell measures the grader, not the skill (design rule 6, the grader visible to the graded). The next outcome eval keeps graders out of the tree until grading.
- Three tasks and one run per cell: a direction, not a measurement of variance.
