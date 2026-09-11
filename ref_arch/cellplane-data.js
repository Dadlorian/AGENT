// Cell-Plane simulation data: workflow Task specifications, status semantics, problem-type registry, rule templates.
export const WL = [
  { id:'refactor', kind:'Codebase refactor', intake:'git event', name:'Monorepo TypeScript strict-mode migration', base:180, group:'cli-', models:['claude-code-cli','cli-cursor-api','cli-cursor-auto'],
    intent:'Enable strict: true in one package of the monorepo and fix every resulting type error without weakening types.',
    acceptance_criteria:'tsc --strict exits 0 · no new @ts-ignore or any · existing tests pass · diff touches one package',
    steps:['Read package + tsconfig','Enable strict, collect errors','Fix errors, no escape hatches','Run tests','Evaluator: criterion check'],
    stuck:[['Tool timeout','pnpm test timed out 3× against 45s ceiling','restart'],['Evaluation FAIL ×2','Identical diff resubmitted after FAIL — agent is looping','redefine'],['No progress','tsc exit 2 unchanged for 6 min','nudge'],['Budget','Ceiling $6.00 reached at step 3','extend']] },
  { id:'research', kind:'Batch research', intake:'schedule', name:'Q3 vendor security posture summaries', base:96, group:'b-', models:['b-google-gemini','b-claude-sonnet','b-deep'],
    intent:"Summarise one vendor's public security documentation into the posture template, citing every claim.",
    acceptance_criteria:'Every claim carries a source URL · template fields all populated · length ≤ 600 words',
    steps:['Fetch sources','Extract claims','Draft summary','Evaluator: citations present'],
    stuck:[['Batch pending','Batch job pending 40+ min, no partial result','nudge'],['Rate limited','Source returned 429 ×5','restart'],['Evaluation FAIL','Summary cites no source for 3 claims','redefine'],['Budget','Ceiling $0.60 reached','extend']] },
  { id:'pipeline', kind:'Data pipeline repair', intake:'HTTP', name:'Nightly ETL: orders → warehouse, failed 02:14', base:14, group:'i-', models:['i-default','i-claude-sonnet','i-fast'],
    intent:'Find why the nightly orders load failed, patch the transform, and re-run the affected partition.',
    acceptance_criteria:'Partition 2026-09-03 loads · row count within 1% of source · no schema change to warehouse',
    steps:['Read failure logs','Isolate failing transform','Patch + dry-run','Re-run partition','Evaluator: row count'],
    stuck:[['Schema drift','Column orders.region missing upstream — patch cannot proceed','redefine'],['Lock','Retry loop on warehouse lock ×7','restart'],['No progress','Same log query issued 4×','escalate']] },
  { id:'review', kind:'Code review + merge', intake:'git event', name:'PR review swarm: release/2026.09', base:42, group:'i-', models:['i-claude-sonnet','i-openai-gpt','i-google-gemini'],
    intent:'Review one pull request for correctness and risk, leave a verdict, and merge if approved by policy.',
    acceptance_criteria:'Verdict is APPROVE or REQUEST_CHANGES · every comment references a line · merge only if policy allows',
    steps:['Fetch diff','Review','Post verdict','Await policy approval gate','Merge'],
    stuck:[['Merge conflict','Rebase failed 3× — conflict in lockfile','nudge'],['Evaluation FAIL','Review posted without a verdict','redefine'],['Policy','OPA denied merge: missing CODEOWNERS approval','park']], parks:true },
  { id:'migration', kind:'Migration with approvals', intake:'CLI', name:'Postgres 16 → 17 tenant migration', base:24, group:'i-', models:['i-claude-opus','i-claude-sonnet'],
    intent:'Migrate one tenant database to Postgres 17 with a verified backup and a rollback path.',
    acceptance_criteria:'pg_dump verified · migration applied · smoke queries match · rollback script present',
    steps:['Backup','Verify backup','Await approval','Apply migration','Smoke test','Evaluator: parity'],
    stuck:[['Budget','Ceiling $4.00 reached during verification','extend'],['Lock','Awaiting tenant write lock 12 min','nudge'],['Tool timeout','pg_dump exceeded 45s ceiling','restart']], parks:true },
  { id:'sched', kind:'Scheduled · RRULE', intake:'FREQ=HOURLY', name:'Hourly dependency CVE sweep', base:12, group:'f-', models:['f-grunt','f-3090-q30','f-5090-q30'],
    intent:"Scan one service's lockfile against the CVE feed and open an issue for any new critical.",
    acceptance_criteria:'Every critical CVE has an issue · no duplicate issues (ledger dedup) · run ≤ 5 min',
    steps:['Pull feed','Diff lockfile','Dedup via ledger','File issues'],
    stuck:[['Overlap','RRULE occurrence overlapped previous run — idempotency key paused','nudge'],['Upstream 503','CVE feed 503 ×4','restart'],['No progress','Local GPU queue saturated','escalate']] },
  { id:'incident', kind:'Incident triage', intake:'HTTP', name:'INC-4471 checkout p99 latency', base:18, group:'i-', models:['i-escalate','i-claude-sonnet','i-fast'],
    intent:'Test one hypothesis for the checkout latency regression and report evidence for or against.',
    acceptance_criteria:'Hypothesis stated · evidence from traces or metrics attached · verdict supported / refuted',
    steps:['State hypothesis','Query traces','Assess','Report'],
    stuck:[['Hypothesis loop','Same trace query issued 4× with no new evidence','escalate'],['Trace unlinked','Root trace unlinked — correlation attribute missing (A7-1)','nudge'],['Budget','Ceiling $4.00 reached','extend']] }
];
export const STATUS = { running:['Running','var(--run)','var(--run-bg)'], waiting:['Waiting','var(--wait)','var(--wait-bg)'], stalled:['Stalled','var(--wait)','var(--wait-bg)'], stuck:['Stuck','var(--stuck)','var(--stuck-bg)'], parked:['Parked','var(--park)','var(--park-bg)'], done:['Done','var(--done)','var(--done-bg)'], cancelled:['Cancelled','var(--done)','var(--done-bg)'] };
export const ORDER = { stuck:0, stalled:1, parked:2, waiting:3, running:4, done:5, cancelled:6 };
export const QUICK = { restart:'Restart sandbox', redefine:'Redefine', nudge:'Nudge', extend:'Raise ceiling', escalate:'Escalate', park:'Approve', approve:'Approve', reject:'Reject', return:'Return', cancel:'Cancel', reassign:'Reassign', undo:'Compensate', hold:'Pause', release:'Resume', dispatch:'Dispatch', rollback:'Rollback', split:'Split', skip:'Skip dependency', grant:'Grant scope', answer:'Answer' };
export const DIAG = { restart:'Same operation, fresh sandbox (microVM). Progress resumes from the last checkpointed step.', redefine:'The loop is in the intent, not the runtime. Tighten the acceptance criteria and replan.', nudge:'Re-send the same intent and acceptance criteria as a new turn. Cheap; try this first.', extend:'budget ceiling terminates the unit, not the platform. Raise it 50% and resume.', escalate:'Move to the i-escalate class. Higher capability, metered.', park:'Policy refused before spend. Approve, reject or return with a note.', approve:'Approval gate in the plan. Release it, or return with a note.', answer:'The agent asked a question and parked itself. Your reply becomes a Task specification annotation.', grant:'Policy denied a scope. A one-time grant is logged with your identity; the rule stays.', rollback:'Return to the previous checkpoint and redo the step with the failed clause quoted.', split:'The unit is too large for its ceiling. Two children inherit the Task specification, each with half the cap plus margin.', skip:'The upstream task will not land. Proceed with its last completed output and mark the edge skipped.', human:'Every automatic rung has been tried. The next fix is a judgement call.' };
export const CAPS = { 'f-':0.0, 'i-':4.0, 'b-':0.6, 'cli-':6.0 };
export const CLASSES = [['f-','free · local','var(--run)'],['i-','interactive','var(--park)'],['b-','batch','var(--wait)'],['cli-','coding CLI','var(--accent)']];
export const STAGES = ['Intake','Build','Verify','Gate','Done'];
export const STAGE_TITLE = { Intake:'Task specification read, plan priced', Build:'Work in the microVM', Verify:'Tests, checks, Evaluator criterion', Gate:'Policy or human approval', Done:'Evaluator PASS, ledger appended' };
export const STALL_AFTER = 40;
export const DESTRUCTIVE = new Set(['cancel','reject']);
export const UNDO_MS = 8000;
export const PROBLEM_TYPE = k => ({ 'Budget':'budget-ceiling','Tool timeout':'tool-timeout','Upstream 503':'tool-timeout','Rate limited':'tool-timeout','Lock':'tool-timeout','No progress':'no-progress','Hypothesis loop':'no-progress','Batch pending':'no-progress','Overlap':'no-progress','Merge conflict':'no-progress','Evaluation FAIL':'evaluation-failed','Evaluation FAIL ×2':'evaluation-failed','Schema drift':'evaluation-failed','Policy':'policy-denied','Approval':'approval-required','Needs input':'needs-input','Returned':'approval-required','Trace unlinked':'trace-unlinked','Stalled':'stalled' })[k] || 'unknown';
export const CRITERIA = { refactor:['tsc --strict exits 0','no new @ts-ignore or any','existing tests pass','diff touches one package'], research:['every claim carries a source URL','template fields all populated','length ≤ 600 words'], pipeline:['partition loads','row count within 1%','no schema change'], review:['verdict present','every comment references a line','merge only if policy allows'], migration:['pg_dump verified','migration applied','smoke queries match','rollback script present'], sched:['every critical CVE has an issue','no duplicate issues','run ≤ 5 min'], incident:['hypothesis stated','evidence attached','verdict supported / refuted'] };
export const RULE_TEMPLATES = [
  { id:'auto-extend', when:'budget-ceiling', then:'extend', label:'When a task hits its budget ceiling, raise ceiling once (+50%)', limit:1 },
  { id:'auto-restart', when:'tool-timeout', then:'restart', label:'When a tool times out, restart the task once', limit:1 },
  { id:'auto-escalate', when:'no-progress', then:'escalate', label:'When progress stops, escalate class once', limit:1 },
  { id:'auto-nudge-stall', when:'stalled', then:'nudge', label:'When a wait passes the stall threshold, nudge', limit:2 },
  { id:'auto-redefine-hint', when:'evaluation-failed', then:'nudge', label:'On Evaluation FAIL, nudge with the failed clause quoted', limit:1 }
];
export const LENSES = [
  { id:'exhausted', group:'Recovery', label:'Exhausted', desc:'Every automatic rung was tried and the problem recurred. These need a judgement call.', match:c => c.exhausted && (c.status === 'stuck' || c.status === 'stalled'), fix:null, hint:'Redefine, split or cancel' },
  { id:'healing', group:'Recovery', label:'Self-healing', desc:'A ladder rung fired and the outcome is not yet scored. No action needed unless it recurs.', match:c => (c.rec && c.rec.history || []).some(h => h.outcome === 'pending' && h.actor !== 'you'), fix:null, hint:'Watching' },
  { id:'input', group:'Governance', label:'Needs input', desc:'The agent asked a question and parked itself. Answer it, or redefine so it does not need to ask.', match:c => c.status === 'parked' && c.stuckInfo && c.stuckInfo[0] === 'Needs input', fix:'answer', hint:'Answer' },
  { id:'budget', group:'Money', label:'Over budget ceiling', desc:'Spend reached the hard budget cap. The unit terminated, not the platform.', match:c => c.stuckInfo && c.stuckInfo[0] === 'Budget', fix:'extend', hint:'Extend +50%' },
  { id:'timeout', group:'Runtime', label:'Timed out', desc:'A tool call exceeded the 45s ceiling or an upstream stopped answering.', match:c => c.stuckInfo && /timeout|503|429|Rate limited|Lock/.test(c.stuckInfo[0] + c.stuckInfo[1]), fix:'restart', hint:'Restart sandbox' },
  { id:'evaluator', group:'Correctness', label:'Evaluation FAIL', desc:'Result did not meet a acceptance-criteria clause, or the same output was resubmitted.', match:c => c.stuckInfo && /Evaluator|Schema drift/.test(c.stuckInfo[0]), fix:'redefine', hint:'Redefine' },
  { id:'loop', group:'Runtime', label:'No progress', desc:'Same query, diff or log request repeated with no new evidence.', match:c => c.stuckInfo && /No progress|Hypothesis loop|Overlap|Merge conflict|Batch pending/.test(c.stuckInfo[0]), fix:'nudge', hint:'Nudge, then escalate' },
  { id:'stalled', group:'Runtime', label:'Stalled', desc:'A wait that passed the threshold. The lease or upstream is not coming back on its own.', match:c => c.status === 'stalled', fix:'nudge', hint:'Nudge, or restart' },
  { id:'dependency', group:'Runtime', label:'Blocked on a task', desc:'Waiting for another task to land. Fix the upstream task, not this one.', match:c => c.dep && (c.status === 'waiting' || c.status === 'stalled') && /dependency/.test(c.waitReason || ''), fix:null, hint:'Open upstream' },
  { id:'policy', group:'Governance', label:'Policy refused', desc:'OPA denied before spend. Needs an approval or a returned note.', match:c => c.status === 'parked' && c.stuckInfo && c.stuckInfo[0] === 'Policy', fix:'approve', hint:'Approve / return' },
  { id:'approval', group:'Governance', label:'Awaiting approval', desc:'Approval gate in the plan. approve.service is waiting on you.', match:c => c.status === 'parked' && c.stuckInfo && c.stuckInfo[0] !== 'Policy' && c.stuckInfo[0] !== 'Needs input', fix:'approve', hint:'Approve' },
  { id:'trace', group:'Telemetry', label:'Trace unlinked', desc:'Root trace not correlated (A7 recommendation 1). Work continues; evidence is orphaned.', match:c => c.stuckInfo && c.stuckInfo[0] === 'Trace unlinked', fix:'nudge', hint:'Nudge with attribute' },
  { id:'waiting', group:'Runtime', label:'Waiting on lease', desc:'Healthy but blocked on a lease or queue. Usually self-resolves before the stall threshold.', match:c => c.status === 'waiting' && !/dependency/.test(c.waitReason || ''), fix:null, hint:'Self-resolving' }
];
export const PROPOSALS = {
  'Tool timeout':['Dispatch config','Raise per-tool ceiling to 120s for this workflow, or split the test step into per-package runs.'],
  'Evaluation FAIL ×2':['Task specification · acceptance criteria','Add "diff must differ from the last FAIL" to the acceptance criteria so the Evaluator rejects resubmission and the agent must change approach.'],
  'Evaluation FAIL':['Task specification · acceptance criteria','Make the failing criterion explicit in the intent, not only the acceptance criteria, so the agent plans for it.'],
  'No progress':['Task specification · steps','Insert a "state what changed since last attempt" step; escalate class automatically after 2 identical turns.'],
  'Budget':['Dispatch config','Raise ceiling for this workflow by 50%, or move it to a cheaper class; current cap is under the median cost-to-done.'],
  'Rate limited':['Dispatch config','Add backoff with jitter at the broker; cap concurrent fetches per host at 2.'],
  'Batch pending':['Dispatch config','Set batch partial-result polling; fall back to i-fast after 45 min pending.'],
  'Schema drift':['Task specification · intent','Add a schema-check pre-step so drift is a typed error (RFC 9457) instead of a stuck task.'],
  'Lock':['Task specification · steps','Acquire the lock as the first step with an idempotency key, and fail fast if paused.'],
  'Merge conflict':['Task specification · steps','Rebase before review, not after verdict; lockfile regenerated by a deterministic step.'],
  'Hypothesis loop':['Task specification · acceptance criteria','Require each turn to cite one new trace id; otherwise Evaluator returns FAIL and the class escalates.'],
  'Trace unlinked':['Dispatch config','Set the correlation attribute at dispatch instead of relying on TRACEPARENT.'],
  'Overlap':['Schedule','Set RRULE occurrence to skip when the previous run holds the idempotency key.'],
  'Upstream 503':['Dispatch config','Retry with exponential backoff; mark the feed degraded after 3 failures instead of stalling.'],
  'Stalled':['Dispatch config','Lower the lease TTL and re-queue on expiry so waits surface as retries, not stalls.']
};
// One glyph per operator verb. Same path everywhere: row, card, detail sheet, bulk bar, ledger.
export const ICONS = {
  nudge:    { path:'M13 8A5 5 0 1 1 11.5 4.5M11.5 2v2.5H9', label:'Nudge', hint:'Re-prompt, same intent' },
  redefine: { path:'M3 13l1-3.5 7-7 2.5 2.5-7 7L3 13zM9.5 4l2.5 2.5', label:'Redefine', hint:'Edit intent / acceptance criteria, replan' },
  escalate: { path:'M4 9l4-4 4 4M4 13l4-4 4 4', label:'Escalate', hint:'Class i-escalate' },
  extend:   { path:'M8 5v6M5 8h6M8 14.5A6.5 6.5 0 1 0 8 1.5a6.5 6.5 0 0 0 0 13z', label:'Raise ceiling', hint:'+50% ceiling' },
  restart:  { path:'M5 4.5a5 5 0 1 0 6 0M8 2v6', label:'Restart sandbox', hint:'Fresh sandbox (microVM), same step' },
  reassign: { path:'M3 5h9l-2.5-2.5M13 11H4l2.5 2.5', label:'Reassign', hint:'Another model class' },
  cancel:   { path:'M4 4l8 8M12 4l-8 8', label:'Cancel', hint:'session/cancel' },
  approve:  { path:'M3 8.5l3.5 3.5L13 4.5', label:'Approve', hint:'Release the approval gate' },
  return:   { path:'M6 4L2.5 7.5 6 11M2.5 7.5H10a3 3 0 0 1 0 6H8', label:'Return with note', hint:'Stays parked' },
  reject:   { path:'M5.5 5.5l5 5M10.5 5.5l-5 5M8 14.5A6.5 6.5 0 1 0 8 1.5a6.5 6.5 0 0 0 0 13z', label:'Reject', hint:'Ends the unit' },
  open:     { path:'M6 3l5 5-5 5', label:'Open', hint:'All actions and the timeline' },
  rollback: { path:'M3 8a5 5 0 1 0 1.5-3.5M3 2v3h3M8 5v3l2 1.5', label:'Rollback', hint:'Resume from an earlier checkpoint' },
  split:    { path:'M8 2v4M8 6l-4 4v4M8 6l4 4v4', label:'Split', hint:'Two smaller units, half the budget ceiling each' },
  skip:     { path:'M3 4l5 4-5 4M8 4l5 4-5 4', label:'Skip dependency', hint:'Decouple, proceed with last completed output' },
  grant:    { path:'M5 8V5.5a3 3 0 0 1 6 0V8M3.5 8h9v6h-9z', label:'Grant scope', hint:'One-time permission, logged' },
  answer:   { path:'M2.5 3.5h11v7H8l-3 3v-3H2.5z', label:'Answer', hint:'Reply to the agent\'s question' },
  human:    { path:'M8 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM3 14a5 5 0 0 1 10 0', label:'Needs you', hint:'Automatic recovery exhausted' }
};
// Recovery ladders: what the platform tries on its own, in order, with a per-rung bound. Anything past the last rung is human work.
export const LADDERS = {
  'tool-timeout':      [['restart', 2], ['reassign', 1]],
  'budget-ceiling':    [['extend', 1], ['split', 1]],
  'no-progress':       [['nudge', 1], ['escalate', 1]],
  'evaluation-failed':        [['nudge', 1], ['rollback', 1]],
  'stalled':           [['nudge', 1], ['restart', 1]],
  'trace-unlinked':    [['nudge', 1]],
  'policy-denied':     [],
  'approval-required': [],
  'needs-input':       []
};
export const LADDER_HUMAN = { 'tool-timeout': 'redefine', 'budget-ceiling': 'redefine', 'no-progress': 'redefine', 'evaluation-failed': 'redefine', 'stalled': 'skip', 'trace-unlinked': 'redefine', 'policy-denied': 'grant', 'approval-required': 'approve', 'needs-input': 'answer' };
export const OUTCOME_AFTER = 12; // ticks before an action is scored resolved / recurred
export const RULE_FOR_KIND = k => RULE_TEMPLATES.find(r => r.when === PROBLEM_TYPE(k));
let seed = 7;
export const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
export const pick = a => a[Math.floor(rnd() * a.length)];
export const money = v => '$' + v.toFixed(2);
export const ago = s => s < 60 ? Math.floor(s) + 's' : s < 3600 ? Math.floor(s / 60) + 'm' : (s / 3600).toFixed(1) + 'h';
export const stageOfStep = (name, i) => /Evaluator|test|Smoke|Verify|Assess|Dedup|Post verdict/i.test(name) ? 'Verify' : /Await/.test(name) ? 'Gate' : i === 0 ? 'Intake' : 'Build';
export const stageOf = (w, c) => c.status === 'done' || c.status === 'cancelled' ? 'Done' : c.status === 'parked' ? 'Gate' : stageOfStep(w.steps[Math.min(c.stepIdx, w.steps.length - 1)], c.stepIdx);
