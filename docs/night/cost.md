# Night Run Token Costs

**Run:** wf_8d4230e8-999
**Agents:** 129
**Total Tokens:** 1,110,376,052

## Breakdown by Model

| Model | Input | Output | Cache Creation | Cache Read | Total |
|-------|-------|--------|-----------------|-----------|-------|
| claude-haiku-4-5-20251001 | 8,232 | 24,300 | 3,401,019 | 47,291,292 | 50,724,843 |
| claude-opus-5 | 13,028 | 627,351 | 16,350,442 | 887,298,896 | 904,289,717 |
| claude-sonnet-5 | 2,690 | 123,516 | 3,880,645 | 151,354,641 | 155,361,492 |

## Method

Extracted usage from all 129 agent JSONL transcripts by grepping for assistant messages with usage fields, then summing:
- input_tokens
- output_tokens
- cache_creation_input_tokens
- cache_read_input_tokens
