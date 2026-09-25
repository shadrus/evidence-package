---
name: evidence-package-handoff
description: >
  Use this skill when you receive an evidence package produced by the
  evidence-package-producer skill — someone else's investigation, hand off
  to you (or to whoever is continuing the work) so they can pick up where
  it left off.
  The skill turns the raw evidence graph into a readable briefing: what's
  solid, what's shaky, what to check first, and what to do next — whatever
  the next phase of the investigation looks like in this domain (code and
  logs for a software incident, additional tests for a medical case,
  underlying records for a financial audit, a site visit for a physical
  investigation, and so on). It also defines how to extend the same
  evidence graph with new findings once they come in, so the whole
  investigation stays in one continuous, traceable chain instead of
  turning into a fresh unstructured report.
---

# Evidence Package Handoff

## Purpose

An evidence package (see evidence-package-producer) documents *how* someone
reached a conclusion, not just the conclusion itself. The point of this
skill is to make that documentation actually useful to whoever receives
it — someone who needs to go from "here's what the evidence shows" to
"here's the actual root cause," continuing in whatever medium this domain
requires — without re-running the whole investigation from scratch, and
without blindly trusting a diagnosis that might have gaps.

This is not a pass/fail validation (that's a different job). The output
here is a briefing a human can read in a couple of minutes, plus, later,
an extension of the same evidence graph once new findings come in.

## Step 1 — Produce a readable briefing

Read the whole package (`conclusion`, `evidence_graph`,
`alternatives_considered`, `verification_hints`) before writing anything.
Then produce a briefing in this shape:

```
## Investigation Handoff: <task.description>

**Claim:** <conclusion.claim, in plain language>
**Confidence:** <conclusion.confidence> — <one line on what this confidence
  is actually about; e.g. "confidence in *which* services are affected,
  not in *why* memory grows">

**Well supported — check again if the decision depends on it:**
- <claim>, backed by <node ids>, cross-confirmed by <independent node ids
  if the same fact is supported by more than one unrelated query>

**Shaky — worth a quick look before trusting this:**
- <claim>, node <id> — <why it's weaker: single data point, reconstructed,
  unconfirmed assumption, etc.>

**Ruled out by the recorded evidence:**
- <hypothesis from alternatives_considered>, ruled out by <evidence_ref>;
  revisit if new evidence or a changed time window makes the test obsolete

**Where to focus next:**
- <concrete next step, in whatever form the next phase of this
  investigation takes>, because <which not_investigated item or weak
  load-bearing claim this addresses>
```

Keep it short. The full graph is still there for anyone who wants to drill
into a specific node — the briefing's job is to save the reader from
having to read all of it just to get oriented.

## Step 2 — Do a quick sanity pass before writing the briefing

Don't take the package's own `verification_hints` at face value — do a
light check first, because the package's author can misjudge these fields
just like anyone else:

- **If `volatile_sources` lists nearly every node**, treat it as
  uninformative rather than as a real warning, and instead judge volatility
  yourself from the queries: a windowed aggregation over a rolling period
  (`increase(...[7d])`, `changes(...[7d])`) will look different if re-run
  later; a point-in-time schema check (`list_metrics`) will not.
- **If most nodes say `supports: conclusion` with an empty
  `derived_from`**, the graph is effectively flat — many of those are
  likely scaffolding steps (discovering what data exists) rather than
  direct evidence for the claim. Read the queries in the order they appear
  to reconstruct the real reasoning chain instead of assuming every node
  independently proves the conclusion.
- **Check whether the obvious alternative was tested for the load-bearing
  claims specifically**, not just for secondary ones. A common gap: an
  alternative explanation gets ruled out for minor findings but never
  gets tested against the claims the conclusion actually depends on.
- **Check `reconstructed_nodes`.** Anything reconstructed goes in the
  "shaky" section of the briefing by default, regardless of how confident
  the wording around it sounds.

None of this is a formal verdict — it's just enough scrutiny to make sure
the briefing doesn't repeat a blind spot the package itself has.

## Step 3 — Turn gaps into concrete next steps

`not_investigated` is close to a ready-made checklist, but usually needs
translating from "what wasn't checked" into "what to actually go look at":

- A conclusion that stops at "what happened" with no established "why" →
  name the specific thing the next step should pull, at the level of
  detail this domain actually has available (the relevant records,
  artifacts, or direct observations around the identified time or
  location, whatever that means here — logs and a memory profile for a
  software incident, a follow-up test for a medical case, the underlying
  transaction records for a financial discrepancy, a site visit for a
  physical investigation), not just "investigate further."
- Prioritize by what's load-bearing. If a claim several other claims
  depend on is still shaky, that's where to start — resolving it either
  confirms or reshapes everything built on top of it.
- If the package flags a metric or count as an approximation (e.g., "this
  proxy assumes X, which might not hold"), that assumption is often the
  fastest place to find the real gap between the diagnosis and the actual
  cause.

## Step 4 — Extending the graph with new findings

As the next person continues the investigation, whatever form that takes
in this domain, append to the same evidence graph so the full chain from
the original evidence to the final answer stays traceable. Continue the
producer's `e{number}` sequence after its highest ID. Never reuse an ID
or start a separate `n{number}` sequence.

Use the producer's EVIDENCE_NODE schema, with `source` naming whatever
produced the finding (a codebase, a lab result, a physical inspection, a
document, an interview, a database record). Include `query` for a
reproducible query or method and `location` for a stable reference; at least
one is required for a sourced finding:

```
EVIDENCE_NODE
id: e{next sequential number}
source: <what produced this finding>
query: <exact query or method, if applicable; otherwise omit>
location: <file:line, commit hash, record ID, or observation reference,
           if applicable; otherwise omit>
result_excerpt: <what was actually found — verbatim or a precise excerpt,
                  with no interpretation>
claim: <what this means>
type: fact | inference | assumption
supports: <id of a node this supports, "conclusion", or "none">
derived_from: <ids of the original evidence nodes that led here, plus any
               nodes added since; empty for direct facts and assumptions>
capture_mode: live
---
```

The same rules from evidence-package-producer still apply here: capture
each finding as you get it, keep `result_excerpt` separate from `claim`,
record negative results too (a place you checked that turned out *not* to
be the cause is valuable context), and use `capture_mode: reconstructed`
honestly if a finding gets written up after the fact instead of in the
moment. Add `ALTERNATIVE_REJECTED` only when evidence rules an explanation
out; an inconclusive check belongs in the graph and unresolved gaps.

## Step 5 — Closing the loop

Once the underlying cause is established, add a new top-level conclusion
rather than editing the original one, so the handoff history stays intact:

```json
{
  "conclusion_update": {
    "claim": "<the root cause, now established>",
    "confidence": "<0..1>",
    "type": "root_cause",
    "derived_from": ["<ids of the nodes added during the follow-up that establish this>"],
    "supersedes": "<the original conclusion.claim, or 'refines' if it
                    narrows rather than replaces it>"
  }
}
```

Append this alongside the original `conclusion` rather than overwriting
it — the original diagnosis (which services, how often) usually still
holds and doesn't need to be re-derived; this just adds the "why" on top
of it.

## What not to do

- Don't rewrite the briefing as a new, self-contained report that drops
  the underlying evidence graph — the value of the package is that the
  next reader can go from the briefing straight into the specific node
  and query that backs any claim they want to double-check.
- Don't silently upgrade a `reconstructed` node to look as trustworthy as
  a `live` one just because it ended up correct — the flag is about how it
  was captured, not whether it turned out right.
- Don't mark something "ruled out" unless evidence actually excludes it
  for the relevant claim and time window. An untested or inconclusive
  alternative belongs in "shaky" or "where to focus next."
- Don't merge multiple follow-up findings into a single node — same
  reasoning as in the producer skill: each finding needs its own id so the
  chain from the original evidence to the final answer stays traceable
  step by step.
