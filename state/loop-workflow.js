// To resume after a mid-section death: relaunch with the same scriptPath and resumeFromRunId from the prior run, not a new startAt.
export const meta = {
  name: 'section-loop',
  description: 'For each manifest section: research (haiku) -> author ideal/implement/use skills (opus) -> ceremony review (sonnet) and improve (opus) -> checkpoint commit/push',
  phases: [
    { title: 'Research', detail: 'one haiku agent per section covering its items, real search results only' },
    { title: 'Author', detail: 'one opus agent per item writing ideal, implement, and use' },
    { title: 'Ceremony', detail: 'sonnet review, then opus improve which also checkpoints (commit, push)' },
  ],
}
// args: { sections: [{name, items:[{name, layer, kb_ids:[...], facets:[skillName...]}]}], brief: path, date: 'YYYY-MM-DD', startAt: sectionIndex }
const SUMMARY = { type: 'object', properties: { ok: { type: 'boolean' }, summary: { type: 'string' }, numbers: { type: 'object' } }, required: ['ok', 'summary'] }
const ROOT = '/home/user/AGENT'
const common = `Work in ${ROOT}. Do not commit or push (a checkpoint agent does that). Skills are data: skill.json per schemas/skill.schema.json, rendered by tools/render_skill.py, checked by tools/validate_skills.py. Every statement is origin=sourced with kb ids and a verbatim quote, or origin=proposed with the word proposed in its text. Never invent a URL, version, fact, or quote. If blocked, apply TARGET.md T5 (1-3-1): define the problem, list the three best goal-aligned solutions, follow the recommendation, and record it; never stop and wait. Date for records: ${args.date}.`

function researchPrompt(section, retry) {
  const list = section.items.map((it, i) => `${i + 1}. ${it.name} (layer ${it.layer}; kb ids ${it.kb_ids.join(', ')})`).join('\n')
  return `${common}
You are the RESEARCH agent for section "${section.name}". Read the brief at ${args.brief} (its research-methodology note if any), state/lessons.jsonl (lessons from previous ceremonies; apply those about research), any kb/ceremonies/section-*-known-issues.json (do not build on skills listed there), TARGET.md, schemas/research.schema.json, and the entries about each item below in docs/research/*.json (grep the item names and kb ids). Items:
${list}
For EACH item: what is the ideal modern state of this area, which standard and version governs it, what do the best implementations do, what are candidate adapters? Run 4 to 8 WebSearch queries per item${retry ? ' (this is a RETRY because the first pass found too little: use different, more specific queries and primary-source domains)' : ''}. WebFetch is blocked for most domains: try it once per item on the single most important URL; status "fetched" only if it returned content, else "search-only".
Write one file per item, kb/research/<item>.jsonl, records conforming to the research schema, ids X-<item>-001 upward, lens "<item>", agent "haiku-research", informs citing the item's kb ids, url/title/snippet copied verbatim from actual search results. Then run: python3 tools/kb.py merge-research
Return JSON: ok, summary (under 100 words: per item, one line with the governing standard), numbers {records_total, records_min_per_item, fetched}.`
}

function authorPrompt(item) {
  const facets = item.facets.map(f => `- ${f.skill} (${f.facet})`).join('\n')
  return `${common}
You are the AUTHOR for the item "${item.name}". Read the brief at ${args.brief}, state/lessons.jsonl (apply lessons about authoring), .claude/skills/agentic-stack/SKILL.md, the manifest entries for each skill below in docs/skill-manifest.json, kb/research/${item.name}.jsonl (run python3 tools/kb.py merge-research first so X- ids are citable), the kb records ${item.kb_ids.join(', ')}, and the skill.json of every skill in the manifest entries' builds_on. Write these skills, in this order, each as .claude/skills/<name>/skill.json:
${facets}
Facet meaning. ideal or discipline: the ideal modern state of the area, governing standard and version (version_status unverified unless a fetched research record shows it), the contract the core imports (operations, shapes as JSON Schema 2020-12, invariants, not_exposed), criteria for judging an implementation; cite research (X- ids, quote from snippet or read) and PASS/TARGET ids. implement: how to build it on our stack, today's adapter from PASS.md Part A, the second adapter per build-adapter-pair (different execution model), migration from what runs, cross-cutting wiring, definition of done with a deliberate breakage (status claimed); adapters[] is the only place product names may appear. use: how a human, an agent, and an event reach it (TARGET T1), minimal inputs and outputs, two worked examples as contract.shapes (origin proposed), the failure shape (RFC 9457 problem details), what it composes with and how enhancing one aspect leaves the rest untouched (T2); if a reader would find it daunting, cut (T3).
composes_with must equal each manifest entry exactly. After each skill: python3 tools/render_skill.py .claude/skills/<name>. At the end: python3 tools/validate_skills.py --only <name> for each of your skills and fix every error. A fact already established in the ideal facet is referenced from implement/use by the skill name and kb id, never re-quoted in fresh wording. Read any kb/ceremonies/section-*-known-issues.json first and do not build on a skill listed there; if one of your builds_on is listed, apply 1-3-1 and record the choice. Keep each skill within 6-15 instructions, 3-10 invariants, 3-8 best practices; long material goes to references/.
Return JSON: ok (validator has zero errors naming your skills), summary (under 80 words), numbers {skills, rows_sourced, rows_proposed}.`
}

function reviewPrompt(section, n, skills, failed) {
  return `${common}
You are the REVIEWER in ceremony ${n} for section "${section.name}". Read TARGET.md, .claude/skills/agentic-stack/SKILL.md, .claude/skills/build-ceremony/SKILL.md if it exists, kb/ceremonies/ceremony-${String(n - 1).padStart(2, '0')}-improve.json if it exists (lessons_for_next_section), and the skill.json of: ${skills.join(', ')} (data only; spot-check ONE SKILL.md against its skill.json to confirm the render matches). Run python3 tools/validate_skills.py once and treat its errors as findings. ${failed && failed.length ? `These items already failed their author's own validation: ${failed.join(', ')}. Start there.` : ''}
Review each against: the seven B1 rules; TARGET T1-T3 (simple, composable, all three entry points); honesty (each sourced quote supports the row's text; proposed rows say proposed; no claimed-to-measured upgrade without a run); usefulness (a fresh author can follow the instructions; the breakage would really fail); size; description triggering; links (composes_with matches the manifest and the ideal/implement/use facets reference each other correctly).
Write kb/ceremonies/ceremony-${String(n).padStart(2, '0')}-review.json with the same shape as ceremony-01-review.json (findings with id C${n}-nnn, severity block|fix|nit, category, location, evidence, suggested_change; metrics; brief_improvements; what_worked). Precision over volume.
Return JSON: ok, summary (under 80 words: counts by severity and the two most important findings), numbers {block, fix, nit, rows_total, rows_sourced, rows_proposed}.`
}

function improvePrompt(section, n) {
  return `${common.replace('Do not commit or push (a checkpoint agent does that).', 'You commit and push at the end.')}
You are the IMPROVER and CHECKPOINT in ceremony ${n} for section "${section.name}". Read kb/ceremonies/ceremony-${String(n).padStart(2, '0')}-review.json, TARGET.md, the brief at ${args.brief}, and each skill.json the findings name.
Apply every block and fix finding, and the nits you agree with, by editing skill.json files (never SKILL.md; never composes_with). Append one row per ceremony to state/lessons.jsonl: {"ceremony":${n},"section":"${section.name}","lessons":[...],"brief_improvements":[...]} (never trimmed); keep the brief a short pointer under 120 lines and only fold in what changes an author's next action. If the findings show a defect in the root contract, the schema rules, or the ceremony discipline itself, fix that too, since the point of the ceremony is that the producing skills improve. Then: python3 tools/render_skill.py --all && python3 tools/validate_skills.py (zero errors; "not written yet" warnings are fine).
Write kb/ceremonies/ceremony-${String(n).padStart(2, '0')}-improve.json in the same shape as ceremony-01-improve.json, including lessons_for_next_section. Append a ledger record: python3 tools/kb.py ledger '{"kind":"ceremony","ceremony":${n},"section":"${section.name}","agent":"opus-improver","result":"<applied/declined/validator>","status":"measured"}'
Then CHECKPOINT: if python3 tools/validate_skills.py still reports errors, write kb/ceremonies/section-${String(n).padStart(2, '0')}-known-issues.json {"section":"${section.name}","broken":[skill names],"errors":[...]} so later agents will not build on them (delete the file if you cleared everything). Run python3 tools/kb.py verify && python3 tools/kb.py ledger-verify && python3 tools/skill_graph.py && write state/loop.json {"last_completed_section":"${section.name}","ceremony":${n}}; git add -A && git commit -m "Section ${section.name}: skills, research, ceremony ${n}" with trailer lines "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" and "Claude-Session: https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96"; git push (retry 4 times with 2s,4s,8s,16s backoff on network errors). Abort the commit if kb verify or ledger-verify failed. Commit with remaining validator errors only when the known-issues file lists them.
Return JSON: ok (pushed), summary (under 80 words: applied, declined, validator line, commit sha, top lesson), numbers {applied, declined, validator_errors}.`
}

const results = []
const start = args.startAt || 0
for (let s = start; s < args.sections.length; s++) {
  const section = args.sections[s]
  const n = s + 1
  log(`Section ${n}/${args.sections.length}: ${section.name} (${section.items.length} items)`)
  let research = await agent(researchPrompt(section, false), { label: `research:${section.name}`, phase: 'Research', schema: SUMMARY, model: 'haiku', effort: 'medium' })
  const minRec = research && research.numbers && research.numbers.records_min_per_item
  if (!research || !research.ok || (typeof minRec === 'number' && minRec < 3)) {
    log(`Section ${n}: research thin (min per item ${minRec}); retrying once with different queries`)
    research = await agent(researchPrompt(section, true), { label: `research-retry:${section.name}`, phase: 'Research', schema: SUMMARY, model: 'haiku', effort: 'medium' })
  }
  const authored = await parallel(section.items.map(item => () =>
    agent(authorPrompt(item), { label: `author:${item.name}`, phase: 'Author', schema: SUMMARY, model: 'opus' })
      .then(a => { log(`  authored ${item.name}: ${a && a.ok ? 'ok' : 'validator errors'}`); return { item: item.name, ok: !!(a && a.ok), summary: a && a.summary } })))
  const skills = section.items.flatMap(i => i.facets.map(f => f.skill))
  const failed = authored.filter(a => a && !a.ok).map(a => a.item)
  const missing = section.items.length - authored.filter(Boolean).length
  if (failed.length || missing) log(`Section ${n}: ${failed.length} items with validator errors${missing ? `, ${missing} author agents died` : ''}: ${failed.join(', ')}`)
  const review = await agent(reviewPrompt(section, n, skills, failed), { label: `review:${section.name}`, phase: 'Ceremony', schema: SUMMARY, model: 'sonnet' })
  const improve = await agent(improvePrompt(section, n), { label: `improve+checkpoint:${section.name}`, phase: 'Ceremony', schema: SUMMARY, model: 'opus' })
  const rec = { section: section.name, skills: skills.length, failed, research: research && research.summary, review: review && review.summary, improve: improve && improve.summary, pushed: !!(improve && improve.ok) }
  results.push(rec)
  log(`Section ${n} done: ${skills.length} skills, pushed=${rec.pushed}`)
  if (!rec.pushed) { log(`Stopping after section ${n}: improve+checkpoint did not push`); break }
}
const wrap = await agent(`${common.replace('Do not commit or push (a checkpoint agent does that).', 'You commit and push at the end.')}
The loop has finished ${results.length} sections. Read every kb/ceremonies/ceremony-*-improve.json and -review.json, state/lessons.jsonl, kb/ceremonies/section-*-known-issues.json, and kb/ledger.jsonl. Write kb/ceremonies/run-summary.json: {"sections":n,"skills_total":n,"applied_total":n,"declined_total":n,"recurring_lessons":[...],"still_broken":[...],"open_questions_carried":[...],"metrics_by_section":[{"section":"...","rows_sourced":n,"rows_proposed":n,"findings":n}]}. Then update README.md's "What is here" table to reflect the actual layers, facets, kb files, and tools (short rows, no prose paragraphs), run python3 tools/skill_graph.py, and git add -A && git commit -m "Run summary and README" (same trailers as before) && git push.
Return JSON: ok, summary (under 120 words for the owner: totals, the three recurring lessons, what is still broken), numbers {skills_total, applied_total, still_broken}.`, { label: 'run-summary', phase: 'Ceremony', schema: SUMMARY, model: 'sonnet' })
return { sections: results, summary: wrap && wrap.summary }
