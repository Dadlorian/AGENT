#!/usr/bin/env python3
"""The mechanisms-beyond-a-plain-completion check (model-access-q2).

A mature build exercises every mechanism a completion call exposes beyond a
bare prompt/response round trip - streaming, a tool-call turn, schema-
constrained structured output, a cache directive, a reasoning-effort setting,
and a usage record splitting prompt/cached/reasoning/completion tokens - on
at least two model adapters, and verifies each one FROM THE RESPONSE rather
than from having merely requested it. A cache hit is read back from
result.cached_tokens after a deliberately repeated prompt, never assumed
because `cache` was set on the request.

    python3 harness/gateway/mechanisms.py            run both adapters, exit 0/1

Python 3.11 standard library only. No product name outside adapters/ (checked
by conformance.py's own product scan; this file adds none).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import CompletionRequest, ModelAccessAdapter, schema_conforms  # noqa: E402
from adapters.dryrun import DryRunAdapter                                     # noqa: E402
from adapters.second import BatchClaimAdapter                                 # noqa: E402

ADAPTERS = {"dryrun": DryRunAdapter, "second": BatchClaimAdapter}
MAX_POLLS = 8

TOOL_SCHEMA = {"type": "object", "required": ["q"], "properties": {"q": {"type": "string"}}}
OUTPUT_SCHEMA = {"type": "object", "required": ["summary", "confidence"],
                 "properties": {"summary": {"type": "string"}, "confidence": {"type": "number"}}}


def ask(model_class="i-fast", prompt="one completion by class", ceiling=200_000, key=None, **extra) -> dict:
    doc = {"model_class": model_class,
           "messages": [{"role": "user", "content": prompt}],
           "idempotency_key": key or ("idem-mech-" + model_class + "-" + str(abs(hash(prompt)) % 10**8)),
           "ceiling_micros": ceiling}
    doc.update(extra)
    return doc


def redeem(adapter: ModelAccessAdapter, doc: dict):
    ticket = adapter.submit(CompletionRequest.from_dict(doc))
    polls = 0
    while ticket.state == "pending" and polls < MAX_POLLS:
        polls += 1
        ticket = adapter.claim(ticket)
    assert ticket.state == "redeemed", f"never redeemed: state={ticket.state} after {polls} polls"
    return ticket


def run(adapter_name: str) -> tuple[list, int, int]:
    adapter = ADAPTERS[adapter_name]()
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            return fn
        return wrap

    @case("streaming: multiple chunks reassemble to the text")
    def _stream():
        ticket = redeem(adapter, ask(prompt="stream this completion", key=f"idem-{adapter_name}-stream-0",
                                     stream=True))
        chunks = ticket.result.stream_chunks
        assert isinstance(chunks, list) and len(chunks) > 1, f"stream_chunks={chunks!r}"
        assert "".join(chunks) == ticket.result.text, "chunks do not reassemble to the response text"
        plain = redeem(adapter, ask(prompt="do not stream this one", key=f"idem-{adapter_name}-stream-off"))
        assert plain.result.stream_chunks is None, "stream_chunks set without stream=True"
        return f"{len(chunks)} chunks, joined == text; unset when stream was not requested"

    @case("tool-call turn: the model defers to a tool, then the turn completes with its result")
    def _tool_turn():
        first = redeem(adapter, ask(prompt="tool: search cafes near the office",
                                    key=f"idem-{adapter_name}-tool-1",
                                    tools=[{"name": "search", "parameters": TOOL_SCHEMA}]))
        calls = first.result.tool_calls
        assert calls and calls[0]["name"] == "search", f"tool_calls={calls!r}"
        assert schema_conforms(TOOL_SCHEMA, calls[0]["arguments"]), \
            f"tool arguments {calls[0]['arguments']!r} do not conform to the tool's own parameter schema"
        assert first.result.text == "", "a turn that calls a tool should not also answer directly"
        followup = {"model_class": "i-fast",
                    "messages": [{"role": "user", "content": "tool: search cafes near the office"},
                                 {"role": "assistant", "content": "calling search"},
                                 {"role": "tool", "content": "3 cafes found within 500m"}],
                    "idempotency_key": f"idem-{adapter_name}-tool-2", "ceiling_micros": 200_000}
        closed = redeem(adapter, followup)
        assert "3 cafes found within 500m" in closed.result.text, \
            f"final turn did not incorporate the tool's own result: {closed.result.text!r}"
        return "turn 1 calls search with schema-conformant arguments; turn 2's text shows the tool result was used"

    @case("schema-constrained structured output validates against the schema it was given")
    def _schema():
        ticket = redeem(adapter, ask(prompt="summarize this", key=f"idem-{adapter_name}-schema-0",
                                     response_schema=OUTPUT_SCHEMA))
        out = ticket.result.structured_output
        assert isinstance(out, dict), f"structured_output={out!r}"
        assert schema_conforms(OUTPUT_SCHEMA, out), f"{out!r} does not conform to {OUTPUT_SCHEMA}"
        # schema_conforms is not vacuously true: a value missing a required field must fail it.
        assert not schema_conforms(OUTPUT_SCHEMA, {"summary": "ok"}), \
            "schema_conforms accepted a value missing a required field"
        assert not schema_conforms(OUTPUT_SCHEMA, {"summary": 5, "confidence": 0.5}), \
            "schema_conforms accepted a wrongly-typed property"
        return f"{out!r} conforms; a value missing a required field or wrongly typed does not"

    @case("cache directive: a hit is observed on a deliberately repeated prompt, not assumed from the flag")
    def _cache():
        prompt = "cache me: the quarterly numbers by region"
        cold = redeem(adapter, ask(prompt=prompt, key=f"idem-{adapter_name}-cache-cold", cache="ephemeral"))
        assert cold.result.cached_tokens == 0, f"a first sighting reported a hit: {cold.result.cached_tokens}"
        warm = redeem(adapter, ask(prompt=prompt, key=f"idem-{adapter_name}-cache-warm", cache="ephemeral"))
        assert warm.result.cached_tokens > 0, "the repeated prompt reported no cache hit"
        assert warm.result.cached_tokens <= warm.result.tokens_in, "cached_tokens exceeds tokens_in"
        uncached = redeem(adapter, ask(prompt=prompt, key=f"idem-{adapter_name}-cache-none"))
        assert uncached.result.cached_tokens == 0, \
            "a repeat with no cache directive reported a hit anyway"
        return f"cold={cold.result.cached_tokens} warm={warm.result.cached_tokens} " \
               f"no-directive={uncached.result.cached_tokens}"

    @case("reasoning effort: raising it produces nonzero reasoning tokens, counted in cost")
    def _reasoning():
        low = redeem(adapter, ask(prompt="think it through", key=f"idem-{adapter_name}-reason-none",
                                  reasoning_effort="none"))
        high = redeem(adapter, ask(prompt="think it through", key=f"idem-{adapter_name}-reason-high",
                                   reasoning_effort="high"))
        assert low.result.reasoning_tokens == 0, f"reasoning_effort=none reported {low.result.reasoning_tokens}"
        assert high.result.reasoning_tokens > 0, "reasoning_effort=high reported no reasoning tokens"
        assert high.result.reasoning_tokens <= high.result.tokens_out, "reasoning_tokens exceeds tokens_out"
        assert high.result.cost_micros > low.result.cost_micros, \
            "raising reasoning effort did not raise cost_micros; reasoning tokens are not counted in cost"
        return f"none={low.result.reasoning_tokens} high={high.result.reasoning_tokens} " \
               f"cost {low.result.cost_micros}->{high.result.cost_micros}"

    @case("usage record: prompt, cached, reasoning and completion tokens are all present and consistent")
    def _usage():
        ticket = redeem(adapter, ask(prompt="usage record shape", key=f"idem-{adapter_name}-usage-0",
                                     reasoning_effort="medium"))
        got = ticket.result
        for field in ("tokens_in", "cached_tokens", "reasoning_tokens", "tokens_out"):
            assert isinstance(getattr(got, field), int), f"{field} is not an int"
        assert got.cached_tokens <= got.tokens_in, "cached_tokens is not a subset of tokens_in (prompt)"
        assert got.reasoning_tokens <= got.tokens_out, "reasoning_tokens is not a subset of tokens_out (completion)"
        return (f"prompt={got.tokens_in} cached={got.cached_tokens} "
               f"reasoning={got.reasoning_tokens} completion={got.tokens_out}")

    passed = sum(1 for s, _ in cases if s == "ok")
    return cases, passed, len(cases)


def main(argv=None) -> int:
    total_pass, total_run = 0, 0
    for name in ("dryrun", "second"):
        cases, passed, ran = run(name)
        print(f"# binding {name}")
        for status, text in cases:
            print(f"  {status:4} {text}")
        total_pass += passed
        total_run += ran
    print(f"mechanisms {'PASSED' if total_pass == total_run else 'FAILED'}: {total_pass}/{total_run} cases, "
         f"2 binding(s), 6 mechanisms each (stream, tool-call turn, structured output, cache, reasoning, usage record)")
    return 0 if total_pass == total_run else 1


if __name__ == "__main__":
    sys.exit(main())
