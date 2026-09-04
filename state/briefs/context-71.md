# Context for the row 71 review (captain's context; the reviewer reads this, docs/fold/plan.json and the skills, nothing else)

What changed: 103 skills were folded into 28 (docs/fold/plan.json). Each target kept its base skill's body; every other former skill is stored whole under `folded` in skill.json and rendered to references/<former>.md with every row and citation intact. Descriptions were rewritten to at most 60 words. Restatement warnings were cleared by naming the sibling row or deleting a row that added nothing. Seven skills had a sourcing pass to bring their proposed share back under 30 percent.

What a review of a folded skill judges, in this order:
1. The description: does it say what the skill does and when to load it, and would it fire for a task that used to land on a folded former skill (its subject must be findable)? Would it fire on a task it should not?
2. Coherence between body and references: a body row that says "`<former>` already states F-nnn" must point at a reference that exists and does state it; a body that contradicts a folded reference is a finding.
3. Duplication that survived: the same operation, invariant or instruction present in the body and in a folded reference without either naming the other.
4. Lost content: compare the target's skill.json against the sources named in docs/fold/plan.json using git (`git show c468ad2^:.claude/skills/<former>/skill.json`); a sourced row present before the fold and absent now, with no deletion recorded in kb/ceremonies/71-polish-*.json or 71-source-*.json, is a block finding.
5. The definition of done: it is the implement facet's; does its criterion still name files that exist, and does the body say how to run it?
6. Everything the ordinary review checks (state/briefs/review.md): misquotes, restatements, uncited claims, descriptions that do not fire on the skill's scope.

Two defects were planted in one skill (tools/plant.py). A review that misses both is discarded and re-run by a different reviewer.
