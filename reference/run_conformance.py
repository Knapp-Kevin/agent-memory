#!/usr/bin/env python3
"""Execute the governed paths and the fixture corpus, then emit a report.

The report conforms to `schemas/conformance-report.schema.json` and covers
three evidence populations: governance paths in `tests/`, the repository's
doctrine fixture corpus driven through authority enforcement, and explicit
forbidden-hit lifecycle assertions that separate discovery, admission, context
surfacing, and downstream influence.

It deliberately claims **conformance level 0**. The doc 06 levels are
cumulative, and this adapter implements neither decay nor calibrated
saturation, so levels 2 and 3 are unmet however well the enforcement checks
do. Every exemption is stated in the report rather than left to be inferred.

Usage:
    python reference/run_conformance.py [-o report.json]
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import unittest
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parent
ROOT = REFERENCE_DIR.parent
sys.path.insert(0, str(REFERENCE_DIR))

from agentmem_ref import fixture_conformance, forbidden_hits, policy, receipts  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, StochasticSelector  # noqa: E402
from agentmem_ref.graphiti_driver import graphiti_available  # noqa: E402
from agentmem_ref.projection_governance import ProjectionGovernor  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402
from agentmem_ref import projections as proj  # noqa: E402

ADAPTER_VERSION = "0.1.0"
DOCTRINE_VERSION = "v0.3"
SUBSTRATE_MODEL = "in-memory temporal graph modelling graphiti-core 0.29.3 verified semantics"
REAL_SUBSTRATE = "graphiti-core 0.29.3 over embedded kuzu, no LLM and no embedder invoked"


def _run_suite() -> tuple[list[str], list[str], list[str]]:
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(REFERENCE_DIR / "tests"), top_level_dir=str(REFERENCE_DIR))
    # Names must be collected before the run: the runner drains the suite.
    names = _collect_names(suite)
    result = unittest.TextTestRunner(verbosity=0, stream=io.StringIO()).run(suite)

    failed = sorted({_short(test) for test, _ in list(result.failures) + list(result.errors)})
    passed = [name for name in names if name not in failed]
    return names, passed, failed


def _collect_names(suite) -> list[str]:
    names: list[str] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            names.extend(_collect_names(item))
        else:
            names.append(_short(item))
    return sorted(names)


def _short(test) -> str:
    return test.id().rsplit(".", 1)[-1]


def _stochastic_sweep(trials: int) -> dict:
    """Sample the permitted set repeatedly and count any escape.

    Stochastic components are judged against an invariant, not against
    identical sampled outputs: the invariant is that no run selects outside
    the authority envelope.
    """
    proposal = policy.Proposal(
        proposal_id="sweep",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference="mem:sweep",
        target_class=policy.M4,
        scope="tenant-a",
        operation="crystallization",
        current_strength="reinforced",
        proposed_strength="canonical",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="high",
        evidence_refs=("ev:1",),
    )
    observed: set[str] = set()
    escapes = 0
    for seed in range(trials):
        adapter = GovernedMemoryAdapter(
            InMemoryTemporalGraph(), tenant="tenant-a", clock=Clock(), selector=StochasticSelector(seed)
        )
        result = adapter.commit_proposal(proposal, "sampled claim")
        selected = result.receipt["selected_action"]
        observed.add(selected)
        if selected not in result.decision.permitted_actions or adapter.containment_violations:
            escapes += 1
    return {"trials": trials, "escapes": escapes, "distinct_actions": sorted(observed)}


def _derived_state_probe() -> dict:
    """Purge a derivation chain and measure residue independently.

    Reports the partition, not a volume. `undeclared_residual` is a hard gate:
    any nonzero value is a failed deletion regardless of how much was removed.
    """
    adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant="tenant-a", clock=Clock())
    governor = ProjectionGovernor(adapter)
    source = "mem:probe"
    adapter.commit_proposal(
        policy.Proposal(
            proposal_id="probe", actor_id="agent:planner", charter_version="c1",
            target_reference=source, target_class=policy.M2, scope="tenant-a",
            operation="promotion", current_strength="reinforced", proposed_strength="promoted",
            downstream_authority=policy.A1, reversibility="reversible", risk_class="low",
            evidence_refs=("ev:1",),
        ),
        "a claim",
    )
    governor.declare("sum:1", (source,), proj.ESTIMATOR_MEDIATED,
                     proj.RECOVERABLE_CONTENT, proj.APPROXIMABLE, "tenant-a")
    governor.declare("sum:2", ("sum:1",), proj.ESTIMATOR_MEDIATED,
                     proj.RECOVERABLE_CONTENT, proj.APPROXIMABLE, "tenant-a")
    governor.declare("export:1", (source,), proj.DETERMINISTIC,
                     proj.RECOVERABLE_CONTENT, proj.IRREPRODUCIBLE, "tenant-a", reachable=False)
    total = 3

    result = governor.purge(
        policy.Proposal(
            proposal_id="probe-purge", actor_id="agent:planner", charter_version="c1",
            target_reference=source, target_class=policy.M2, scope="tenant-a",
            operation="permanent_deletion", current_strength="promoted",
            proposed_strength="not_applicable", downstream_authority=policy.A1,
            reversibility="irreversible", risk_class="low", evidence_refs=("ev:1",),
            approval_refs=("approval:dpo",), review_satisfied=True,
        ),
        source,
    )
    return {
        "buckets": result.buckets,
        "undeclared_count": len(result.undeclared),
        "derived_total": total,
        "hard_gate_passed": result.hard_gate_passed,
    }


def _exemptions(substrate_executed: bool) -> list[str]:
    common = [
        "No conformance level is claimed. The corpus is driven through the adapter's authority "
        "enforcement, but doc 06 levels are cumulative and this adapter implements neither decay "
        "nor calibrated saturation, so levels 2 and 3 are unmet regardless of enforcement results.",
        "Retrieval ranking is lexical rather than hybrid, so recall quality is not measured "
        "and no calibration claim is made.",
        "The policy implements the subset of the decision table these paths require.",
        "Forbidden-hit coverage proves the named negative classes and blocking stages only. It does "
        "not imply that unlisted lifecycle, sensitivity, purpose, or downstream-action classes are covered.",
    ]
    if not substrate_executed:
        return common + [
            "The real substrate is not installed, so only substrate-model paths ran. "
            "Model execution is a precondition, not runtime evidence."
        ]
    return common + [
        "Substrate paths executed against an embedded backend deprecated upstream, chosen because "
        "it needs no server. No governance behavior under test depends on the backend.",
        "Node topology is simplified to one edge per fact; this exercises governance invariants, "
        "not knowledge modelling.",
    ]


def build_report(trials: int = 200) -> dict:
    substrate_executed = graphiti_available()
    names, passed, failed = _run_suite()
    corpus = fixture_conformance.run()
    forbidden = forbidden_hits.run()
    sweep = _stochastic_sweep(trials)
    derived = _derived_state_probe()
    report = {
        "schema_version": "1.0.0",
        "implementation": "agent-memory reference governed adapter",
        "version": ADAPTER_VERSION,
        "doctrine_version": DOCTRINE_VERSION,
        "policy_version": policy.POLICY_VERSION,
        "conformance_level": 0,
        "fixtures_run": corpus["fixtures_run"],
        "fixtures_passed": corpus["fixtures_passed"],
        "fixtures_failed": corpus["fixtures_failed"],
        "trials_run": (
            len(names)
            + len(corpus["fixtures_run"])
            + len(forbidden["assertions_run"])
            + sweep["trials"]
        ),
        "metrics": {
            "stochastic_action_set_violation_rate": sweep["escapes"] / max(sweep["trials"], 1),
            "deletion_residue_rate": derived["undeclared_count"] / max(derived["derived_total"], 1),
        },
        "forbidden_hit_coverage": forbidden["coverage"],
        "known_exemptions": _exemptions(substrate_executed) + fixture_conformance.exemptions(),
        "known_failures": corpus["fixtures_failed"] + failed + forbidden["failures"],
        "metric_extensions": {
            "substrate_model": SUBSTRATE_MODEL,
            "real_substrate_executed": substrate_executed,
            "real_substrate": REAL_SUBSTRATE if substrate_executed else None,
            "governance_paths_executed": len(names),
            "negative_paths_executed": len([name for name in names if "positive" not in name]),
            "governance_paths_failed": failed,
            "corpus_fixtures_with_authority_envelope": corpus["fixtures_with_authority_envelope"],
            "forbidden_hit_assertions_run": len(forbidden["assertions_run"]),
            "forbidden_hit_classes_covered": forbidden["forbidden_classes"],
            "forbidden_hit_failures": forbidden["failures"],
            "stochastic_trials": sweep["trials"],
            "stochastic_escapes": sweep["escapes"],
            "stochastic_distinct_actions": sweep["distinct_actions"],
            "derived_state_residue_buckets": derived["buckets"],
            "derived_state_hard_gate_passed": derived["hard_gate_passed"],
        },
    }
    receipts.validate("conformance-report.schema.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", help="Write the report here instead of stdout.")
    parser.add_argument("--trials", type=int, default=200, help="Stochastic containment trials (default 200).")
    args = parser.parse_args()

    report = build_report(trials=args.trials)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Wrote conformance report to {args.output}")
    else:
        print(rendered, end="")
    if report["metric_extensions"]["stochastic_escapes"]:
        print("stochastic containment violated", file=sys.stderr)
        return 1
    if not report["metric_extensions"]["derived_state_hard_gate_passed"]:
        print("undeclared deletion residue detected", file=sys.stderr)
        return 1
    return 1 if report["known_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
