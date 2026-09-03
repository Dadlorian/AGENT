#!/usr/bin/env python3
"""Scheduling: when a recurring unit of work is due, as a pure function.

Read it in this order. RRULE_PATTERN and parse_rule() are the grammar gate: a
declaration passes through here or it is refused before any adapter sees it.
occurrences() and next_after() are the pure evaluator cap-scheduling requires
(F-b3-15): rule, anchor, IANA zone and a window in, an ordered de-duplicated
occurrence set out, reading no clock and touching no store. They are the one
correctness surface every adapter shares -- an adapter differs in how it
DECLARES a unit and FIRES an occurrence, never in how it computes one
(cap-scheduling-implement: "occurrences and next_after are served by the
platform's own evaluator, because the engine offers no pure call the vector
corpus can drive"). SchedulingAdapter is the interface the core imports:
declare() and fire() are concrete here so no adapter can build its own
envelope or skip the rule-part refusal at declare time; occurrences,
next_after and tick are what an adapter's execution model actually differs on.

No product name appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only: datetime, zoneinfo, calendar, re, hashlib.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

INTERFACE_VERSION = "0.1"

# --- Typed failures: RFC 9457 problem details, closed registry (T-t9-02) ---
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "Declaration is not a well-formed RRULE", False),
    "unsupported-rule-part": (422, "This adapter refuses a rule part it cannot evaluate", False),
    "adapter-unavailable": (503, "The engine that owns this schedule cannot be reached", True),
}


class Problem(Exception):
    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,
                     "detail": detail, "retryable": retryable, **ext}
        super().__init__(detail)


# --- The RRULE grammar gate (cap-scheduling ScheduleDeclaration.recurrence) -
RRULE_PATTERN = re.compile(r"^FREQ=[A-Z]+(;[A-Z]+=[^;]+)*$")
SUPPORTED_PARTS = {"FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTH",
                   "BYMONTHDAY", "BYSETPOS", "BYHOUR", "BYMINUTE", "BYSECOND"}
SUPPORTED_FREQ = {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}
WEEKDAY = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
BYDAY_TOKEN = re.compile(r"^([+-]?\d{1,2})?(MO|TU|WE|TH|FR|SA|SU)$")


def parse_rule(rule: str) -> dict:
    """A declared string in, a part dict out. The one gate every rule passes
    (cap-scheduling: "describes a repeating schedule as a single string")."""
    if not isinstance(rule, str) or not RRULE_PATTERN.match(rule):
        raise Problem("document-invalid",
                      f"{rule!r} is not FREQ=...;PART=value;... — RFC 5545 RRULE grammar", rule=rule)
    parts: dict[str, str] = {}
    for chunk in rule.split(";"):
        key, _, value = chunk.partition("=")
        if key in parts:
            raise Problem("document-invalid", f"rule part {key} repeated", rule=rule)
        parts[key] = value
    if parts["FREQ"] not in SUPPORTED_FREQ:
        raise Problem("unsupported-rule-part",
                      f"FREQ={parts['FREQ']} is outside {sorted(SUPPORTED_FREQ)}",
                      rule=rule, unsupported_parts=["FREQ=" + parts["FREQ"]])
    unsupported = sorted(set(parts) - SUPPORTED_PARTS)
    if unsupported:
        raise Problem("unsupported-rule-part",
                      f"rule part(s) {unsupported} are not evaluated by this adapter",
                      rule=rule, unsupported_parts=unsupported)
    return parts


def _zone(tzname: str) -> ZoneInfo:
    try:
        return ZoneInfo(tzname)
    except ZoneInfoNotFoundError as exc:
        raise Problem("document-invalid", f"{tzname!r} is not an IANA zone", timezone=tzname) from exc


def _parse_instant(text: str) -> datetime:
    """A window bound or UNTIL: ISO 8601, 'Z' or an explicit offset, always UTC-aware here."""
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise Problem("document-invalid", f"{text!r} has no offset; window bounds are instants, not wall time")
    return dt.astimezone(timezone.utc)


def _parse_anchor(text: str) -> datetime:
    """starts_at: a naive wall-clock reading in the declared zone (cap-scheduling:
    'the first instant the rule counts from'). A trailing Z or offset is stripped:
    the zone field, not the anchor string, carries the zone (F-b3-15)."""
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return dt.replace(tzinfo=None)


def _byday_tokens(value: str) -> list[tuple[int | None, int]]:
    out = []
    for token in value.split(","):
        m = BYDAY_TOKEN.match(token)
        if not m:
            raise Problem("document-invalid", f"BYDAY token {token!r} is not N?WEEKDAY")
        n = int(m.group(1)) if m.group(1) else None
        out.append((n, WEEKDAY[m.group(2)]))
    return out


def _month_dates(year: int, month: int, parts: dict, anchor_day: int) -> list[date]:
    """The candidate day-of-month set for one (year, month), before BYSETPOS."""
    days_in_month = calendar.monthrange(year, month)[1]
    if "BYMONTHDAY" in parts:
        out = []
        for tok in parts["BYMONTHDAY"].split(","):
            n = int(tok)
            d = n if n > 0 else days_in_month + n + 1
            if 1 <= d <= days_in_month:
                out.append(date(year, month, d))
        return sorted(out)
    if "BYDAY" in parts:
        out = []
        for n, wd in _byday_tokens(parts["BYDAY"]):
            matches = [date(year, month, d) for d in range(1, days_in_month + 1)
                      if date(year, month, d).weekday() == wd]
            if n is None:
                out.extend(matches)
            elif n > 0 and n <= len(matches):
                out.append(matches[n - 1])
            elif n < 0 and -n <= len(matches):
                out.append(matches[n])
        return sorted(set(out))
    # Neither given: recur on the anchor's own day-of-month; an invalid date
    # (30 Feb, 31 Apr) is silently absent that month/year — RFC 5545 semantics,
    # and how a 29 Feb rule with no BYMONTHDAY quietly skips non-leap years.
    return [date(year, month, anchor_day)] if anchor_day <= days_in_month else []


def _apply_setpos(dates: list[date], parts: dict) -> list[date]:
    if "BYSETPOS" not in parts or not dates:
        return dates
    dates = sorted(dates)
    out = []
    for tok in parts["BYSETPOS"].split(","):
        n = int(tok)
        idx = n - 1 if n > 0 else n
        if -len(dates) <= idx < len(dates):
            out.append(dates[idx])
    return sorted(set(out))


def _times_of_day(parts: dict, anchor: datetime) -> list[tuple[int, int, int]]:
    hours = [int(h) for h in parts["BYHOUR"].split(",")] if "BYHOUR" in parts else [anchor.hour]
    minutes = [int(m) for m in parts["BYMINUTE"].split(",")] if "BYMINUTE" in parts else [anchor.minute]
    seconds = [int(s) for s in parts["BYSECOND"].split(",")] if "BYSECOND" in parts else [anchor.second]
    return sorted({(h, m, s) for h in hours for m in minutes for s in seconds})


def generate(rule: str, starts_at: str, tzname: str):
    """The pure generator: yields ascending UTC instants for a rule, one
    period at a time, honouring COUNT and UNTIL, forever otherwise. A caller
    bounds it (occurrences bounds by window, next_after by count); this
    function itself never stops on its own unless the rule does.
    """
    parts = parse_rule(rule)
    freq = parts["FREQ"]
    interval = int(parts.get("INTERVAL", "1"))
    if interval < 1:
        raise Problem("document-invalid", "INTERVAL must be a positive integer")
    count = int(parts["COUNT"]) if "COUNT" in parts else None
    until = _parse_instant(parts["UNTIL"]) if "UNTIL" in parts else None
    anchor = _parse_anchor(starts_at)
    zone = _zone(tzname)
    times = _times_of_day(parts, anchor)
    bymonth = {int(m) for m in parts["BYMONTH"].split(",")} if "BYMONTH" in parts else None

    emitted = 0

    def to_utc(d: date, hms: tuple[int, int, int]) -> datetime:
        # fold=0: PEP 495's default, the earlier of an ambiguous fall-back pair
        # and the search-forward reading Python gives a spring-forward gap.
        # cap-scheduling-implement names this a research question, not settled
        # here; fold=0 is stated so the corpus can assert against it directly.
        local = datetime(d.year, d.month, d.day, *hms, fold=0, tzinfo=zone)
        return local.astimezone(timezone.utc)

    if freq == "DAILY":
        d = anchor.date()
        step = 0
        while True:
            if step % interval == 0 and (bymonth is None or d.month in bymonth):
                for hms in times:
                    if d == anchor.date() and hms < (anchor.hour, anchor.minute, anchor.second):
                        continue
                    instant = to_utc(d, hms)
                    if until and instant > until:
                        return
                    yield instant
                    emitted += 1
                    if count is not None and emitted >= count:
                        return
            d += timedelta(days=1)
            step += 1

    elif freq == "WEEKLY":
        week_start = anchor.date() - timedelta(days=anchor.weekday())
        step = 0
        while True:
            if step % interval == 0:
                if "BYDAY" in parts:
                    weekdays = sorted({wd for _, wd in _byday_tokens(parts["BYDAY"])})
                else:
                    weekdays = [anchor.weekday()]
                days = [week_start + timedelta(days=wd) for wd in weekdays
                       if bymonth is None or (week_start + timedelta(days=wd)).month in bymonth]
                for d in sorted(days):
                    if d < anchor.date():
                        continue
                    for hms in times:
                        if d == anchor.date() and hms < (anchor.hour, anchor.minute, anchor.second):
                            continue
                        instant = to_utc(d, hms)
                        if until and instant > until:
                            return
                        yield instant
                        emitted += 1
                        if count is not None and emitted >= count:
                            return
            week_start += timedelta(days=7)
            step += 1

    elif freq == "MONTHLY":
        year, month = anchor.year, anchor.month
        step = 0
        while True:
            if step % interval == 0:
                days = _apply_setpos(_month_dates(year, month, parts, anchor.day), parts)
                for d in days:
                    if d < anchor.date():
                        continue
                    for hms in times:
                        if d == anchor.date() and hms < (anchor.hour, anchor.minute, anchor.second):
                            continue
                        instant = to_utc(d, hms)
                        if until and instant > until:
                            return
                        yield instant
                        emitted += 1
                        if count is not None and emitted >= count:
                            return
            month += 1
            if month == 13:
                month = 1
                year += 1
            step += 1

    elif freq == "YEARLY":
        year = anchor.year
        step = 0
        while True:
            if step % interval == 0:
                months = sorted(bymonth) if bymonth else [anchor.month]
                days: list[date] = []
                for m in months:
                    days.extend(_month_dates(year, m, parts, anchor.day))
                days = _apply_setpos(sorted(set(days)), parts)
                for d in days:
                    if d < anchor.date():
                        continue
                    for hms in times:
                        if d == anchor.date() and hms < (anchor.hour, anchor.minute, anchor.second):
                            continue
                        instant = to_utc(d, hms)
                        if until and instant > until:
                            return
                        yield instant
                        emitted += 1
                        if count is not None and emitted >= count:
                            return
            year += 1
            step += 1


MAX_PERIODS_SCANNED = 20_000   # the safety cap; only unbounded rules can hit it


@dataclass(frozen=True)
class OccurrenceSet:
    recurrence: str
    timezone: str
    window: dict
    occurrences: list  # ISO 'Z' strings, ascending, de-duplicated
    truncated: bool = False

    def as_dict(self) -> dict:
        return {"recurrence": self.recurrence, "timezone": self.timezone,
                "window": self.window, "occurrences": self.occurrences, "truncated": self.truncated}


def occurrences(rule: str, starts_at: str, tzname: str, window_from: str, window_to: str) -> OccurrenceSet:
    """(rule, anchor, zone, window) -> OccurrenceSet. Pure: no clock, no store."""
    frm, to = _parse_instant(window_from), _parse_instant(window_to)
    if to <= frm:
        raise Problem("document-invalid", "window.to must be after window.from")
    parts = parse_rule(rule)
    unbounded = "COUNT" not in parts and "UNTIL" not in parts
    out: list[str] = []
    scanned = 0
    truncated = False
    seen = set()
    for instant in generate(rule, starts_at, tzname):
        scanned += 1
        if instant >= to:
            break
        if instant >= frm and instant not in seen:
            seen.add(instant)
            out.append(instant.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if scanned >= MAX_PERIODS_SCANNED:
            truncated = unbounded
            break
    return OccurrenceSet(rule, tzname, {"from": window_from, "to": window_to}, out, truncated)


def next_after(rule: str, starts_at: str, tzname: str, after: str) -> str | None:
    """The first occurrence strictly after `after`, or None when the rule is
    exhausted. Does not materialise a window (cap-scheduling: 'the read a
    caller needs to answer when does this run next')."""
    cutoff = _parse_instant(after)
    scanned = 0
    for instant in generate(rule, starts_at, tzname):
        scanned += 1
        if instant > cutoff:
            return instant.strftime("%Y-%m-%dT%H:%M:%SZ")
        if scanned >= MAX_PERIODS_SCANNED:
            return None
    return None


# --- Declarations and firing (cap-scheduling ScheduleDeclaration, fire) -----
@dataclass(frozen=True)
class ScheduleDeclaration:
    unit_ref: str
    recurrence: str
    starts_at: str
    timezone: str
    catch_up: str = "skip"       # skip | fire_once | fire_all
    trigger: dict | None = None

    @classmethod
    def from_dict(cls, doc: dict) -> "ScheduleDeclaration":
        required = {"unit_ref", "recurrence", "starts_at", "timezone", "catch_up"}
        missing = sorted(required - set(doc))
        if missing:
            raise Problem("document-invalid", f"missing required field(s) {missing}")
        if doc["catch_up"] not in ("skip", "fire_once", "fire_all"):
            raise Problem("document-invalid", f"catch_up {doc['catch_up']!r} is not skip|fire_once|fire_all")
        parse_rule(doc["recurrence"])           # refused here, not silently accepted
        _zone(doc["timezone"])
        return cls(doc["unit_ref"], doc["recurrence"], doc["starts_at"], doc["timezone"],
                   doc["catch_up"], doc.get("trigger"))


def idempotency_key(unit_ref: str, occurrence_instant: str) -> str:
    """Derived from unit + occurrence, never from the wall clock at firing
    time (cap-scheduling-implement step 6): a late catch-up fire of the same
    occurrence reuses this key rather than minting a new one."""
    return "sched-" + hashlib.sha256(f"{unit_ref}|{occurrence_instant}".encode()).hexdigest()[:24]


def build_envelope(declaration: ScheduleDeclaration, occurrence_instant: str, actor: str,
                   budget_ceiling_micros: int, run_id: str, correlation_id: str) -> dict:
    """The one envelope builder every adapter shares (cap-scheduling-implement
    step 5: 'Give no adapter its own envelope builder'). kind is always
    schedule; the occurrence enters exactly as a human, event or external
    entry would (T-t6-02)."""
    return {
        "envelope_version": "0.1", "kind": "schedule",
        "entry_id": f"schedule-{declaration.unit_ref}-{occurrence_instant.replace(':', '').replace('-', '')}",
        "occurred_at": occurrence_instant,
        "actor": {"subject": f"schedule:{declaration.unit_ref}",
                  "delegation_chain": [{"actor": f"schedule:{declaration.unit_ref}", "obtained_via": "workload_attestation"},
                                       {"actor": actor, "obtained_via": "token_exchange"}]},
        "intent": {"workflow_ref": declaration.unit_ref,
                  "summary": f"recurrence {declaration.recurrence} fired for {declaration.unit_ref}"},
        "correlation": {"run_id": run_id, "correlation_id": correlation_id, "depth": 0},
        "budget": {"ceiling_micros": budget_ceiling_micros, "currency": "USD", "on_exceed": "terminate_unit"},
        "idempotency_key": idempotency_key(declaration.unit_ref, occurrence_instant),
        "payload": {"recurrence": declaration.recurrence, "occurrence": occurrence_instant,
                   "source_kind": "recurrence rule fired", "catch_up": declaration.catch_up},
    }


@dataclass
class ConformanceReport:
    """RecurrenceConformanceReport, the shape cap-scheduling-implement's
    definition_of_done asserts against."""
    adapter: str
    selected_by: str
    vectors_run: int
    mismatches: int
    corpus_covers: list
    adapters_run: int = 1
    unsupported_parts: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"adapter": self.adapter, "selected_by": self.selected_by,
                "vectors_run": self.vectors_run, "mismatches": self.mismatches,
                "corpus_covers": self.corpus_covers, "adapters_run": self.adapters_run,
                "unsupported_parts": self.unsupported_parts}


class SchedulingAdapter(ABC):
    """One recurrence interface: occurrences, next_after, declare, fire, tick.

    declare and fire are concrete here so no adapter can build its own
    envelope or skip the rule-part refusal (cap-scheduling-implement step 5
    and step 8). occurrences and next_after default to the shared pure
    evaluator above -- the platform's own evaluator this file exists to be --
    which an adapter overrides only when its execution model genuinely
    computes them differently (T-t7-02: adapters differ in plumbing, not in
    what the standard means).
    """

    entity = "adapter"
    adapter_name = "unset"          # in-engine-schedule | standalone-evaluator (skill's enum)
    selected_by = "configuration"   # a const: no code path chooses an adapter (F-b1-04)
    declared_gaps: tuple = ()

    def __init__(self):
        self.declared = 0
        self.fired = 0
        self.refused = 0
        self._declarations: dict[str, ScheduleDeclaration] = {}
        self._fired_keys: dict[str, dict] = {}   # idempotency_key -> envelope, for replay

    # 1/2. occurrences, next_after -- the shared pure evaluator by default
    def occurrences(self, rule: str, starts_at: str, tzname: str, window_from: str, window_to: str) -> OccurrenceSet:
        return occurrences(rule, starts_at, tzname, window_from, window_to)

    def next_after(self, rule: str, starts_at: str, tzname: str, after: str) -> str | None:
        return next_after(rule, starts_at, tzname, after)

    # 3. declare -- refuses a rule part this adapter cannot evaluate
    def declare(self, doc: dict) -> ScheduleDeclaration:
        decl = ScheduleDeclaration.from_dict(doc)
        parts = parse_rule(decl.recurrence)
        blocked = sorted(set(parts) & set(self.declared_gaps))
        if blocked:
            self.refused += 1
            raise Problem("unsupported-rule-part",
                          f"{self.entity} does not evaluate {blocked}",
                          rule=decl.recurrence, unsupported_parts=blocked)
        result = self._declare(decl)          # counted only once this actually succeeds
        self.declared += 1
        self._declarations[decl.unit_ref] = decl
        return result

    @abstractmethod
    def _declare(self, decl: ScheduleDeclaration) -> ScheduleDeclaration:
        """Adapter-specific registration. Reached only after the gate holds."""

    # 4. fire -- one occurrence in, the shared envelope out, always
    def fire(self, unit_ref: str, occurrence_instant: str, actor: str = "user:corey",
             budget_ceiling_micros: int = 500_000, run_id: str | None = None,
             correlation_id: str | None = None) -> dict:
        decl = self._declarations.get(unit_ref)
        if decl is None:
            raise Problem("document-invalid", f"{unit_ref!r} was never declared on this adapter")
        key = idempotency_key(unit_ref, occurrence_instant)
        if key in self._fired_keys:
            return self._fired_keys[key]              # replay: the same envelope, no second fire
        rid = run_id or ("run-" + key[6:18])
        cid = correlation_id or ("corr-" + key[6:18])
        envelope = build_envelope(decl, occurrence_instant, actor, budget_ceiling_micros, rid, cid)
        self._fire(decl, envelope)
        self.fired += 1
        self._fired_keys[key] = envelope
        return envelope

    @abstractmethod
    def _fire(self, decl: ScheduleDeclaration, envelope: dict) -> None:
        """Adapter-specific hand-off of an already-built envelope. Never
        builds or edits the envelope itself (step 5)."""

    # 5. tick -- the only clock reader in the capability (proposed operation)
    @abstractmethod
    def tick(self, now: str, window_s: int) -> list:
        """now, window_s -> the envelopes fired for every declared unit whose
        evaluator reports an occurrence inside [now, now+window_s)."""


def problem_to_dict(problem: Problem) -> dict:
    return problem.body


parse_instant = _parse_instant   # public: adapters compute tick windows with it
