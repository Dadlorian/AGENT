export const meta = {
  name: 'section-loop',
  description: 'For each manifest section: research (haiku) -> author ideal/implement/use skills (opus) -> ceremony review (sonnet) and improve (opus) -> checkpoint commit/push',
  phases: [
    { title: 'Research', detail: 'one haiku agent per item, real search results only' },
    { title: 'Author', detail: 'one opus agent per skill facet' },
    { title: 'Ceremony', detail: 'sonnet review, opus improve, checkpoint' },
  ],
}
// args: { sections: [{name, items:[{name, layer, kb_ids:[...], facets:[skillName...]}]}], brief: path, date: 'YYYY-MM-DD', startAt: sectionIndex }
const SUMMARY = { type: 'object', properties: { ok: { type: 'boolean' }, summary: { type: 'string' }, numbers: { type: 'object' } }, required: ['ok', 'summary'] }
const ROOT = '/home/user/AGENT'
const common = `Work in ${ROOT}. Do not commit or push (a checkpoint agent does that). Skills are data: skill.json per schemas/skill.schema.json, rendered by tools/render_skill.py, checked by tools/validate_skills.py. Every statement is origin=sourced with kb ids and a verbatim quote, or origin=proposed with the word proposed in its text. Never invent a URL, version, fact, or quote. Date for records: ${args.date}.`

function researchPrompt(item) {
  return `${common}
You are a RESEARCH agent for the item "${item.name}" (layer ${item.layer}). Read TARGET.md, schemas/research.schema.json, the kb records ${item.kb_ids.join(', ')} via python3 tools/kb.py show <id>, and the entries about this item in docs/research/*.json (grep the item's name and its kb ids).
Question: what is the ideal modern state of this area, which standard and version governs it, what do the best implementations do, and what are the candidate adapters? Run 6 to 12 WebSearch queries. WebFetch is blocked for most domains: try it on the single most important URL; status is "fetched" only if it returned content, else "search-only".
Write kb/research/${item.name}.jsonl: one record per line conforming to the research schema, ids X-${item.name}-001 upward, lens "${item.name}", agent "haiku-research", informs citing the kb ids above. url/title/snippet copied verbatim from actual search results. Then run: python3 tools/kb.py merge-research
Return JSON: ok, summary (under 80 words: what the ideal state is and the governing standard), numbers {records, fetched}.`
}

function authorPrompt(item, skill, facet) {
  const facetText = {
    ideal: 'the IDEAL definition of this area: what the ideal modern state is, the governing standard and version (version_status unverified unless a fetched research record shows it), the contract the core imports (operations, shapes as JSON Schema 2020-12, invariants, not_exposed), criteria for judging an implementation. Cite research records (X- ids, quote from snippet or read) and PASS/TARGET ids.',
    implement: 'HOW TO IMPLEMENT it on our stack: today\'s adapter from PASS.md Part A, the second adapter chosen per build-adapter-pair (different execution model), migration from what runs today, wiring of the cross-cutting concerns, and a definition of done with a deliberate breakage (status claimed). adapters[] is the only place product names may appear.',
    use: 'HOW A COMPOSER USES it (TARGET T2, T3): how a human, an agent, and an event reach it, the minimal inputs and outputs, two worked examples as contract.shapes (origin proposed), the failure shape (RFC 9457 problem details), what it composes with and how enhancement of one aspect leaves the rest untouched. Simplicity is a requirement: if a reader would find it daunting, cut.',
  }[facet]
  return `${common}
You are an AUTHOR. Read the brief at ${args.brief}, then .claude/skills/agentic-stack/SKILL.md, the manifest entry for "${skill}" in docs/skill-manifest.json, kb/research/${item.name}.jsonl (cite by X- id; run python3 tools/kb.py merge-research first so they are citable), the kb records ${item.kb_ids.join(', ')}, and the skill.json of every skill in your manifest entry's builds_on.
Write .claude/skills/${skill}/skill.json covering ${facetText}
composes_with must equal the manifest entry exactly. Then: python3 tools/render_skill.py .claude/skills/${skill} && python3 tools/validate_skills.py. Fix every error naming ${skill}; ignore "not written yet" warnings and errors about other skills still being written.
Return JSON: ok (validator has zero errors naming this skill), summary (under 60 words), numbers {rows_sourced, rows_proposed, instructions}.`
}

function reviewPrompt(section, n, skills) {
  return `${common}
You are the REVIEWER in ceremony ${n} for section "${section.name}". Read TARGET.md, .claude/skills/agentic-stack/SKILL.md, .claude/skills/build-ceremony/SKILL.md if it exists, kb/ceremonies/ceremony-${String(n - 1).padStart(2, '0')}-improve.json if it exists (lessons_for_next_section), and the skill.json plus SKILL.md of: ${skills.join(', ')}.
Review each against: the seven B1 rules; TARGET T1-T3 (simple, composable, all three entry points); honesty (each sourced quote supports the row's text; proposed rows say proposed; no claimed-to-measured upgrade without a run); usefulness (a fresh author can follow the instructions; the breakage would really fail); size; description triggering; links (composes_with matches the manifest and the ideal/implement/use facets reference each other correctly).
Write kb/ceremonies/ceremony-${String(n).padStart(2, '0')}-review.json with the same shape as ceremony-01-review.json (findings with id C${n}-nnn, severity block|fix|nit, category, location, evidence, suggested_change; metrics; brief_improvements; what_worked). Precision over volume.
Return JSON: ok, summary (under 80 words: counts by severity and the two most important findings), numbers {block, fix, nit, rows_total, rows_sourced, rows_proposed}.`
}

function improvePrompt(section, n) {
  return `${common}
You are the IMPROVER in ceremony ${n} for section "${section.name}". Read kb/ceremonies/ceremony-${String(n).padStart(2, '0')}-review.json, TARGET.md, the brief at ${args.brief}, and each skill.json the findings name.
Apply every block and fix finding, and the nits you agree with, by editing skill.json files (never SKILL.md; never composes_with). Fold brief_improvements into the brief file in place (keep it under 120 lines). If the findings show a defect in the root contract, the schema rules, or the ceremony discipline itself, fix that too, since the point of the ceremony is that the producing skills improve. Then: python3 tools/render_skill.py --all && python3 tools/validate_skills.py (zero errors; "not written yet" warnings are fine).
Write kb/ceremonies/ceremony-${String(n).padStart(2, '0')}-improve.json in the same shape as ceremony-01-improve.json, including lessons_for_next_section. Append a ledger record: python3 tools/kb.py ledger '{"kind":"ceremony","ceremony":${n},"section":"${section.name}","agent":"opus-improver","result":"<applied/declined/validator>","status":"measured"}'
Return JSON: ok, summary (under 80 words: applied, declined, validator result, top lesson), numbers {applied, declined, validator_errors}.`
}

function checkpointPrompt(section, n) {
  return `${common.replace('Do not commit or push (a checkpoint agent does that).', 'You ARE the checkpoint agent: you commit and push.')}
Section "${section.name}" (ceremony ${n}) is complete. Run, in order: python3 tools/kb.py verify; python3 tools/kb.py ledger-verify; python3 tools/validate_skills.py (must be zero errors; if not, report and do not commit); python3 tools/skill_graph.py; python3 tools/kb.py ledger '{"kind":"checkpoint","section":"${section.name}","agent":"checkpoint","result":"<validator line>","status":"measured"}'; then git add -A && git commit -m "Section ${section.name}: skills, research, ceremony ${n}" with the trailer lines "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" and "Claude-Session: https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96"; then git push (retry up to 4 times with 2s,4s,8s,16s backoff on network errors). Also write state/loop.json: {"last_completed_section": "${section.name}", "ceremony": ${n}, "commit": "<sha>"}.
Return JSON: ok (pushed), summary (under 60 words: skill count, validator line, commit sha), numbers {skills, errors, warnings}.`
}

const results = []
const start = args.startAt || 0
for (let s = start; s < args.sections.length; s++) {
  const section = args.sections[s]
  const n = s + 1
  log(`Section ${n}/${args.sections.length}: ${section.name} (${section.items.length} items)`)
  // per item: research, then its facets in parallel; items pipeline independently
  const authored = await pipeline(section.items,
    item => agent(researchPrompt(item), { label: `research:${item.name}`, phase: 'Research', schema: SUMMARY, model: 'haiku', effort: 'medium' }),
    (r, item) => parallel(item.facets.map(f => () =>
      agent(authorPrompt(item, f.skill, f.facet), { label: `author:${f.skill}`, phase: 'Author', schema: SUMMARY, model: 'opus' })
        .then(a => ({ skill: f.skill, ok: a && a.ok, summary: a && a.summary, research: r && r.summary }))))
  )
  const skills = section.items.flatMap(i => i.facets.map(f => f.skill))
  const failed = authored.flat().filter(a => a && !a.ok).map(a => a.skill)
  if (failed.length) log(`Section ${n}: ${failed.length} skills reported validator errors: ${failed.join(', ')} (reviewer will see them)`)
  const review = await agent(reviewPrompt(section, n, skills), { label: `review:${section.name}`, phase: 'Ceremony', schema: SUMMARY, model: 'sonnet' })
  const improve = await agent(improvePrompt(section, n), { label: `improve:${section.name}`, phase: 'Ceremony', schema: SUMMARY, model: 'opus' })
  const checkpoint = await agent(checkpointPrompt(section, n), { label: `checkpoint:${section.name}`, phase: 'Ceremony', schema: SUMMARY, model: 'haiku', effort: 'low' })
  const rec = { section: section.name, skills: skills.length, failed, review: review && review.summary, improve: improve && improve.summary, checkpoint: checkpoint && checkpoint.summary, pushed: !!(checkpoint && checkpoint.ok) }
  results.push(rec)
  log(`Section ${n} done: ${skills.length} skills, pushed=${rec.pushed}`)
  if (!rec.pushed) { log(`Stopping after section ${n}: checkpoint did not push`); break }
}
return results
