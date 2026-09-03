# Document shapes, step vocabulary and worked examples

Long material for `core-document`. Everything here is **proposed** unless a kb id is given beside it.
The skill body is enough to declare a document and to judge an implementation; open this file only when
writing the full schema, the step vocabulary or the fixture corpus.

Resolve every id below with `python3 tools/kb.py show <id>`.

## 1. Full document schema (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:document:0.1",
  "title": "Document",
  "description": "Declared intent, definition of done, steps (F-b2-02). Written before anything reads it.",
  "type": "object",
  "additionalProperties": false,
  "required": ["document_version", "document_id", "intent", "definition_of_done", "steps"],
  "properties": {
    "document_version": {"const": "0.1"},
    "document_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{2,63}$"},
    "supersedes": {
      "type": "string",
      "description": "document_id of the declaration this one replaces. A document is never edited in place."
    },
    "declared_by": {
      "type": "string",
      "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$",
      "description": "The subject that declared it. Never the entry kind."
    },
    "intent": {
      "type": "object",
      "additionalProperties": false,
      "required": ["summary"],
      "properties": {
        "summary": {"type": "string", "minLength": 1, "maxLength": 400},
        "rationale": {"type": "string", "maxLength": 2000},
        "not_in_scope": {"type": "array", "items": {"type": "string"}}
      }
    },
    "definition_of_done": {
      "type": "array",
      "minItems": 1,
      "items": {"$ref": "urn:agentic:core:document:check:0.1"}
    },
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": {"$ref": "#/$defs/step"}
    }
  },
  "$defs": {
    "step": {
      "type": "object",
      "additionalProperties": false,
      "required": ["step_id", "op"],
      "properties": {
        "step_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{1,47}$"},
        "op": {"enum": ["sequence", "parallel", "loop", "approval", "agent", "judge"]},
        "good_at": {"type": "string", "description": "What the step needs done, not which agent does it."},
        "inputs": {"type": "array", "items": {"type": "string"}},
        "children": {"type": "array", "items": {"$ref": "#/$defs/step"}},
        "checks": {
          "type": "array",
          "items": {"type": "string"},
          "description": "check_id values from definition_of_done that close this step."
        }
      }
    }
  }
}
```

## 2. Step vocabulary (proposed, closed)

The operator names are the six the reference consumption example publishes in
`examples/end-to-end/schemas/workflow.schema.json`. `core-document` records the vocabulary; the
composition layer owns its semantics.

| Operator | The step declares | Not declared here |
|---|---|---|
| `sequence` | children run in order, each seeing the results before it | how results are passed |
| `parallel` | independent branches, fanned in when all return | branch scheduling |
| `loop` | a repeated child with a bound | the bound's enforcement |
| `approval` | the work parks until a person returns a decision | where the person is reached |
| `agent` | what the step is good at, and its model class | which agent or vendor serves it |
| `judge` | which `check_id` grades the step | the criterion text (design rule 6, F-b1-07) |

## 3. Risk tiers (proposed)

| `risk_tier` | Evidence the check must produce | Behavioural check required |
|---|---|---|
| `low` | command output and exit status | no |
| `standard` | output plus a count of things actually checked | yes, at least one |
| `high` | the `standard` evidence plus a recorded run of the declared `breakage` | yes, and the breakage must have been observed to fail |

`behavioural_run == 0` yields `outcome: "inconclusive"` at every tier (see the check-report shape in the
skill body).

## 4. Worked example A: a human declares a fault fix (proposed)

```json
{
  "document_version": "0.1",
  "document_id": "fix-auth-timeout",
  "declared_by": "user:corey",
  "intent": {"summary": "Sessions drop after 60s on the auth service; find the cause and fix it."},
  "definition_of_done": [
    {
      "check_id": "regression-passes",
      "kind": "behavioural",
      "risk_tier": "high",
      "command": "pytest tests/test_auth_timeout.py -q",
      "expected": "1 passed, exit 0",
      "breakage": "revert the fix; the test must fail"
    }
  ],
  "steps": [
    {"step_id": "triage", "op": "agent", "good_at": "naming the failing component from a fault report"},
    {"step_id": "fix", "op": "loop", "children": [
      {"step_id": "edit", "op": "agent", "good_at": "editing named files until a named test passes"},
      {"step_id": "grade", "op": "judge", "checks": ["regression-passes"]}
    ]}
  ]
}
```

## 5. Worked example B: an event declares the same work (proposed)

The alert body differs; the document does not. Only `declared_by` changes, and it is outside the digest.

```json
{
  "document_version": "0.1",
  "document_id": "fix-auth-timeout",
  "declared_by": "service:alerting",
  "intent": {"summary": "Sessions drop after 60s on the auth service; find the cause and fix it."},
  "definition_of_done": [
    {
      "check_id": "regression-passes",
      "kind": "behavioural",
      "risk_tier": "high",
      "command": "pytest tests/test_auth_timeout.py -q",
      "expected": "1 passed, exit 0",
      "breakage": "revert the fix; the test must fail"
    }
  ],
  "steps": [
    {"step_id": "triage", "op": "agent", "good_at": "naming the failing component from a fault report"},
    {"step_id": "fix", "op": "loop", "children": [
      {"step_id": "edit", "op": "agent", "good_at": "editing named files until a named test passes"},
      {"step_id": "grade", "op": "judge", "checks": ["regression-passes"]}
    ]}
  ]
}
```

Both documents canonicalise to the same digest. That equality is the property the C1 fixture corpus and
the `document-validate` run in the skill's definition of done exist to protect.

## 6. Worked example C: an agent declares the same work (proposed)

TARGET T1 lists three ways in (T-t1-01, T-t1-02, T-t1-03), so the third producer gets an instance too. A
partner agent that found the fault while running its own checks declares it directly; no human is present.
`declared_by` follows the delegation-chain naming the entry envelope uses (`agent:<name>`), and it is
outside the digest, so this document is byte-for-byte the same declaration as A and B once canonicalised.

```json
{
  "document_version": "0.1",
  "document_id": "fix-auth-timeout",
  "declared_by": "agent:partner-sre-bot",
  "intent": {"summary": "Sessions drop after 60s on the auth service; find the cause and fix it."},
  "definition_of_done": [
    {
      "check_id": "regression-passes",
      "kind": "behavioural",
      "risk_tier": "high",
      "command": "pytest tests/test_auth_timeout.py -q",
      "expected": "1 passed, exit 0",
      "breakage": "revert the fix; the test must fail"
    }
  ],
  "steps": [
    {"step_id": "triage", "op": "agent", "good_at": "naming the failing component from a fault report"},
    {"step_id": "fix", "op": "loop", "children": [
      {"step_id": "edit", "op": "agent", "good_at": "editing named files until a named test passes"},
      {"step_id": "grade", "op": "judge", "checks": ["regression-passes"]}
    ]}
  ]
}
```

A, B and C are the three producers of the same declaration. The only field that differs is `declared_by`,
and nothing downstream may branch on it.

## 7. Worked example D: the failure shape (proposed)

What a declarer receives when the document is refused. cap-errors owns the shape and its registry
(F-b3-13); `core-document` adds no failure format of its own, and this instance is what the invariant
"every rejection of a document is a typed problem, not prose" looks like on the wire. The rejected
declaration is the negative corpus in miniature: no `definition_of_done`, and criterion text smuggled into
a step payload, which design rule 6 forbids (F-b1-07).

```json
{
  "sent": {
    "document_version": "0.1",
    "document_id": "fix-auth-timeout",
    "declared_by": "user:corey",
    "intent": {"summary": "Sessions drop after 60s on the auth service; find the cause and fix it."},
    "steps": [
      {"step_id": "edit", "op": "agent", "good_at": "fix it",
       "criterion": "passes when pytest tests/test_auth_timeout.py reports 1 passed"}
    ]
  },
  "received_on_the_wire": {
    "media_type": "application/problem+json",
    "type": "urn:agentic:problem:document-invalid",
    "title": "Document failed schema validation",
    "status": 422,
    "detail": "2 violations; see errors",
    "retryable": false,
    "instance": "urn:agentic:core:document:fix-auth-timeout",
    "errors": [
      {
        "instance_location": "",
        "keyword_location": "/required",
        "message": "required property 'definition_of_done' is missing"
      },
      {
        "instance_location": "/steps/0/criterion",
        "keyword_location": "/$defs/step/additionalProperties",
        "message": "property 'criterion' is not allowed"
      }
    ]
  },
  "what_the_declarer_does": "adds the definition-of-done check and deletes the criterion from the step, in one edit; there is no second round of discovery"
}
```

Both violations arrive together because validation is one pass (see the skill body, instruction 6), and the
caller branches on `type`, never on the wording of `detail` or `message`. The second violation is why the
step schema in section 1 sets `additionalProperties: false`: rule 6 is enforced by the shape, not by review.

## 8. Fixture corpus (proposed)

| Corpus | Count | Contains |
|---|---|---|
| `fixtures/positive/` | 12 | minimal one-step document; every operator once; superseding document; both examples above |
| `fixtures/negative/` | 9 | `missing-dod.json`, `criterion-in-payload.json`, empty `steps`, unknown `op`, unknown `risk_tier`, `checks` naming no declared `check_id`, `additionalProperties` at the root, mutated `document_version`, `summary` over 400 characters |
