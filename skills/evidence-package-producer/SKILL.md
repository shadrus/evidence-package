---
name: evidence-package-producer
description: >
  Use only when the user asks for a verifiable evidence package, an audit
  trail of an investigation, or a reproducible record to hand off for
  independent review. Capture each source result and its interpretation
  immediately, then deliver a structured evidence graph with the conclusion.
  Do not trigger for ordinary research, browsing, analysis, or a request
  for a concise answer merely because external sources are consulted.
---

# Producer Skill: Building a Verifiable Evidence Package

## Why this exists

A typical investigation output is just text, and it has to be re-verified
from scratch because it's unclear exactly which source queries back the
conclusion, or whether the full set of relevant data was considered versus
just a convenient subset. This skill's job is to make sure the final
conclusion ships with a chain of evidence suitable for independent
verification.

Key constraint: evidence must be captured **at the moment it is obtained**,
not reconstructed at the end. If you do the whole analysis first and then
try to "recall" what supported the conclusion, that doesn't work — facts
almost always get unconsciously fitted to an already-formed conclusion
(confirmation bias), and real findings get lost or distorted along the way.

## Core principle: capture in the moment, not after

This rule applies throughout the entire task, from the first source query
to the final conclusion:

> As soon as you receive a result from any data source (a metrics query, a
> log search, a database read, an API call, reading a document, etc.) —
> **before taking the next reasoning step** — record it as an EVIDENCE_NODE
> in the format below. Do not defer the recording "for later," and do not
> merge several results into a single node after the fact.

This applies even when a result seems minor or doesn't support your current
hypothesis — especially in that case; see the rejected-hypotheses section
below.

## EVIDENCE_NODE format

Emit this block as plain text during your reasoning, immediately after
receiving a result from a source:

```
EVIDENCE_NODE
id: e{sequential number}
source: <system/source, e.g. "Prometheus", "Loki", "internal API">
query: <exact query or method, if applicable; otherwise omit>
location: <stable file:line, record ID, commit, document reference, or
           observation location, if applicable; otherwise omit>
result_excerpt: <what the source actually returned — verbatim or a precise
                  excerpt, with no interpretation>
claim: <what you believe this means — your interpretation>
type: fact | inference | assumption
supports: <id of a node this supports, "conclusion", or "none" if the
           result did not support a claim>
derived_from: <ids of the nodes this was logically derived from, if this
               is an inference; empty for a fact>
capture_mode: live
---
```

Field notes:

- Use one `e{number}` sequence for the entire investigation. A recipient
  continues after the largest existing number; never restart at `e1` or
  switch prefixes. References in `supports` and `derived_from` use these IDs.
- Include at least one reproducible locator, `query` or `location`, for a
  sourced finding; include both when useful. For an unsourced assumption,
  name the assumption in `claim` and leave `result_excerpt` empty.

- **result_excerpt** must be kept separate from **claim**. The former is
  literally what the source returned. The latter is your interpretation.
  Don't blend them into one field — whoever validates the package needs to
  be able to judge the interpretation independently of the raw fact.
- **type**:
  - `fact` — a direct observation from the source, nothing inferred.
  - `inference` — a conclusion logically derived from one or more other
    nodes (list them in `derived_from`).
  - `assumption` — something you're taking as given without verification
    (e.g. "the 14:03 deploy was the only change in the window"). These
    nodes get separately flagged in the final package as needing the
    validator's attention.
- **supports: none** — don't skip negative results. A query that returned
  nothing is still a node. Lack of support alone does not disprove a
  hypothesis; distinguish "not tested sufficiently" from "ruled out."

## Protocol for rejected hypotheses

If evidence rules out a considered hypothesis, record that explicitly.
If the available data merely fails to support it, keep it as an open
question in `verification_hints.not_investigated` and record the result;
do not call it rejected:

```
ALTERNATIVE_REJECTED
hypothesis: <what the hypothesis was>
evidence_ref: <id(s) of the node(s) that rule it out>
reason: <short explanation>
---
```

This distinguishes an alternative that was ruled out from one that was
considered but remains unresolved.

## If live capture was missed

You may sometimes notice that the conclusion relies on something that
wasn't recorded at the moment it was obtained (you skipped a step, mentally
combined several sources, etc.). Don't try to hide this by reconstructing
the node as if it had been created on time. Instead, create it with an
honest flag:

```
EVIDENCE_NODE
...
capture_mode: reconstructed
reconstruction_note: <why this node wasn't captured at the time>
---
```

`capture_mode: reconstructed` is not an error and not a reason to redo the
work. It's a signal to the validator that this particular node needs
priority re-checking, because it carries less trust than a `live` node.

## Self-check before the final conclusion

Before formulating the `conclusion`, go through every claim it rests on
and explicitly answer, for each one:

1. Does an EVIDENCE_NODE already exist for this claim, created earlier in
   this reasoning? If yes, reference its id — don't create a duplicate.
2. If no node exists, create one now with `capture_mode: reconstructed`,
   as described above.
3. Are there alternative explanations you didn't check and didn't record
   as `ALTERNATIVE_REJECTED`? If so, either check them now, or explicitly
   note in the package that they were never investigated — don't leave
   this silent.
4. Which nodes are actually load-bearing for the conclusion (without them
   it falls apart), and which are background context? Flag the former as
   load-bearing in the final package.

## The final package

Once the analysis is done, assemble the final package **from the
EVIDENCE_NODE and ALTERNATIVE_REJECTED blocks already produced during your
reasoning** — don't rewrite or alter their content at this step, only
compile them:

```json
{
  "task": {
    "description": "<brief description of the analysis task>",
    "timestamp": "<when the analysis was performed>"
  },
  "conclusion": {
    "claim": "<the final conclusion>",
    "confidence": "<0..1, your confidence estimate>",
    "type": "root_cause | recommendation | diagnosis | other"
  },
  "evidence_graph": [
    { "...": "all EVIDENCE_NODE blocks captured during the work, as-is" }
  ],
  "alternatives_considered": [
    { "...": "all ALTERNATIVE_REJECTED blocks" }
  ],
  "verification_hints": {
    "load_bearing": ["<ids of nodes the conclusion cannot stand without>"],
    "reconstructed_nodes": ["<ids of nodes with capture_mode: reconstructed>"],
    "volatile_sources": ["<ids of nodes whose sources may change/expire — logs with TTL, etc.>"],
    "not_investigated": ["<untested or inconclusively checked alternatives and open aspects>"]
  }
}
```

The `reconstructed_nodes` field in `verification_hints` is populated
automatically from whichever nodes got a `capture_mode: reconstructed`
flag — no need to decide this again, just compile the list.

## What not to do

- Don't merge several distinct source queries into one EVIDENCE_NODE "for
  brevity" — each query gets its own node, otherwise the validator can't
  reproduce exactly what you checked.
- Don't rewrite the `result_excerpt` of an already-created node if you
  later interpret it differently — create a new `inference` node that
  references it via `derived_from`; the original fact stays unchanged.
- Don't skip recording a result just because it "didn't matter" — the
  absence of confirmation is information the validator needs too.
- Don't relabel `capture_mode: reconstructed` as `live`, even when the
  difference seems minor — the validator relies on this flag to prioritize
  what to re-check.
