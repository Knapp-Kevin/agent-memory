"""Pinned LangGraph lifecycle comparator for issue #208.

The comparator uses LangGraph's real StateGraph, InMemorySaver, checkpoint
history, checkpoint replay, and RetryPolicy while keeping Agent Memory
governance in the existing reference adapter. No model or external service is
needed because the claim under test is lifecycle/checkpoint interoperability.
"""

from __future__ import annotations

from importlib.metadata import version as package_version
from typing import Any, TypedDict

from ..runtime.adapter import GovernedMemoryAdapter, RecallContext
from ..memory.framework_lifecycle import (
    MutationReplayGuard,
    build_framework_lifecycle_event,
    classify_checkpoint_relation,
)
from ..core.policy import A1, A5, M2, M5, Proposal
from ..state.substrate import InMemoryTemporalGraph

LANGGRAPH_PACKAGE = "langgraph==1.2.11"
LANGGRAPH_VERSION = "1.2.11"
LANGGRAPH_CHECKPOINT_PACKAGE = "langgraph-checkpoint==4.2.0"
LANGGRAPH_CHECKPOINT_VERSION = "4.2.0"
LANGGRAPH_TAG = "1.2.11"
LANGGRAPH_COMMIT = "644815f9e5bc52ad8f7a5227a456227e9c3e639b"
LANGGRAPH_SOURCE_REF = "github:langchain-ai/langgraph@1.2.11"
WORKFLOW_REF = "langgraph:stategraph:agent-memory-lifecycle-v0.1"
SCOPE = "scope:tenant-a/project-a"
TENANT = "tenant-a"
PROJECT = "project-a"

try:  # Optional dependency, installed only by the dedicated comparator workflow.
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import RetryPolicy

    _LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - keeps core/reference imports dependency-free
    InMemorySaver = None  # type: ignore[assignment]
    StateGraph = None  # type: ignore[assignment]
    START = "__start__"  # type: ignore[assignment]
    END = "__end__"  # type: ignore[assignment]
    RetryPolicy = None  # type: ignore[assignment]
    _LANGGRAPH_AVAILABLE = False


class LifecycleState(TypedDict, total=False):
    mode: str
    phase: str
    recall_admitted: bool
    status: str
    receipt_ref: str
    decision_outcome: str


def _proposal(
    *,
    proposal_id: str,
    target_reference: str,
    operation: str = "promotion",
    target_class: str = M2,
    downstream_authority: str = A1,
    current_strength: str = "observed",
    proposed_strength: str = "promoted",
    risk_class: str = "low",
    reversibility: str = "reversible",
) -> Proposal:
    return Proposal(
        proposal_id=proposal_id,
        actor_id="actor:langgraph",
        charter_version="charter:langgraph-v1",
        target_reference=target_reference,
        target_class=target_class,
        scope=SCOPE,
        operation=operation,
        current_strength=current_strength,
        proposed_strength=proposed_strength,
        downstream_authority=downstream_authority,
        reversibility=reversibility,
        risk_class=risk_class,
        evidence_refs=(f"evidence:{proposal_id}",),
        tenant_ref=TENANT,
        purpose="framework-lifecycle-proof",
        isolation_domain_refs=(SCOPE,),
        project_ref=PROJECT,
    )


def _seed_proposal() -> Proposal:
    return _proposal(
        proposal_id="proposal:langgraph:seed",
        target_reference="mem:langgraph:seed",
    )


def _allowing_proposal() -> Proposal:
    return _proposal(
        proposal_id="proposal:langgraph:allow-1",
        target_reference="mem:langgraph:lifecycle",
    )


def _retry_proposal() -> Proposal:
    return _proposal(
        proposal_id="proposal:langgraph:retry-1",
        target_reference="mem:langgraph:retry",
    )


def _denied_proposal() -> Proposal:
    return _proposal(
        proposal_id="proposal:langgraph:deny-1",
        target_reference="mem:langgraph:protected",
        operation="scope_expansion",
        target_class=M5,
        downstream_authority=A5,
        current_strength="promoted",
        proposed_strength="canonical",
        risk_class="critical",
        reversibility="irreversible",
    )


def _write_count(substrate: InMemoryTemporalGraph) -> int:
    return sum(1 for operation, _ in substrate.write_log if operation == "write_fact")


def _checkpoint_id(config: dict[str, Any] | None) -> str | None:
    if not config:
        return None
    configurable = config.get("configurable")
    if not isinstance(configurable, dict):
        return None
    value = configurable.get("checkpoint_id")
    return value if isinstance(value, str) and value else None


def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


class LifecycleNodes:
    def __init__(
        self,
        *,
        memory: GovernedMemoryAdapter,
        replay_guard: MutationReplayGuard,
    ) -> None:
        self.memory = memory
        self.replay_guard = replay_guard
        self.post_commit_failure_emitted = False

    def recall(self, state: LifecycleState) -> LifecycleState:
        cross_scope = state.get("mode") == "cross_scope"
        context = RecallContext(
            target_domain_refs=("scope:tenant-b/project-b",) if cross_scope else (SCOPE,),
            principal_ref="principal:langgraph",
            project_ref="project-b" if cross_scope else PROJECT,
            purpose="framework-lifecycle-proof",
        )
        recall = self.memory.governed_recall("governed seed", context)
        return {
            "phase": "recalled",
            "recall_admitted": bool(recall.admitted),
        }

    def mutate(self, state: LifecycleState) -> LifecycleState:
        mode = state.get("mode")
        if mode == "allow":
            return self._allow(state, key="langgraph:allow:mutation-1", proposal=_allowing_proposal())
        if mode == "retry":
            key = "langgraph:retry:mutation-1"
            prior = self.replay_guard.prior_receipt(key)
            if prior is not None:
                return {
                    "phase": "replayed",
                    "status": "replay_after_retry",
                    "receipt_ref": prior,
                    "recall_admitted": bool(state.get("recall_admitted")),
                }
            result = self.memory.commit_proposal(_retry_proposal(), "langgraph retry governed fact")
            if not result.committed:
                raise RuntimeError(f"retry-path governed mutation unexpectedly refused: {result.refusal}")
            receipt_ref = result.receipt["receipt_id"]
            self.replay_guard.record(key, receipt_ref)
            if not self.post_commit_failure_emitted:
                self.post_commit_failure_emitted = True
                # This deliberately fails after the Agent Memory commit but before
                # LangGraph can persist this node's successful output. Retry must
                # consult the stable receipt rather than commit again.
                raise ConnectionError("simulated post-commit LangGraph node failure")
            return {
                "phase": "committed",
                "status": "committed",
                "receipt_ref": receipt_ref,
                "recall_admitted": bool(state.get("recall_admitted")),
            }
        if mode == "deny":
            result = self.memory.commit_proposal(_denied_proposal(), "must never persist")
            return {
                "phase": "denied",
                "status": "denied" if not result.committed else "unexpected_commit",
                "decision_outcome": result.decision.outcome,
                "recall_admitted": bool(state.get("recall_admitted")),
            }
        if mode == "cross_scope":
            return {
                "phase": "completed",
                "status": "cross_scope_observed",
                "recall_admitted": bool(state.get("recall_admitted")),
            }
        raise ValueError(f"unsupported LangGraph lifecycle mode {mode!r}")

    def _allow(self, state: LifecycleState, *, key: str, proposal: Proposal) -> LifecycleState:
        prior = self.replay_guard.prior_receipt(key)
        if prior is not None:
            return {
                "phase": "replayed",
                "status": "replay",
                "receipt_ref": prior,
                "recall_admitted": bool(state.get("recall_admitted")),
            }
        result = self.memory.commit_proposal(proposal, "langgraph lifecycle governed fact")
        if not result.committed:
            raise RuntimeError(f"governed mutation unexpectedly refused: {result.refusal}")
        receipt_ref = result.receipt["receipt_id"]
        self.replay_guard.record(key, receipt_ref)
        return {
            "phase": "committed",
            "status": "committed",
            "receipt_ref": receipt_ref,
            "recall_admitted": bool(state.get("recall_admitted")),
        }


def _build_graph(memory: GovernedMemoryAdapter, replay_guard: MutationReplayGuard, saver: Any):
    nodes = LifecycleNodes(memory=memory, replay_guard=replay_guard)
    builder = StateGraph(LifecycleState)
    builder.add_node("recall", nodes.recall)
    builder.add_node(
        "mutate",
        nodes.mutate,
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_interval=0.01,
            backoff_factor=1.0,
            jitter=False,
            retry_on=ConnectionError,
        ),
    )
    builder.add_edge(START, "recall")
    builder.add_edge("recall", "mutate")
    builder.add_edge("mutate", END)
    return builder.compile(checkpointer=saver), nodes


def _history(graph: Any, config: dict[str, Any]) -> list[Any]:
    return list(graph.get_state_history(config))


def _checkpoint_lineage(history: list[Any]) -> dict[str, str | None]:
    lineage: dict[str, str | None] = {}
    for snapshot in history:
        current = _checkpoint_id(snapshot.config)
        if current is None:
            continue
        lineage[current] = _checkpoint_id(getattr(snapshot, "parent_config", None))
    return lineage


def _find_pre_mutation_snapshot(history: list[Any]) -> Any:
    for snapshot in history:
        values = getattr(snapshot, "values", {})
        next_nodes = tuple(getattr(snapshot, "next", ()))
        if isinstance(values, dict) and values.get("phase") == "recalled" and "mutate" in next_nodes:
            if _checkpoint_id(snapshot.config) is not None:
                return snapshot
    raise AssertionError("LangGraph history did not contain a checkpoint before the mutation node")


def run_comparator(agent_memory_commit: str) -> dict[str, Any]:
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise ValueError("agent_memory_commit must be an exact lowercase 40-hex commit")
    if not _LANGGRAPH_AVAILABLE:
        raise RuntimeError(f"{LANGGRAPH_PACKAGE} is required for the pinned comparator")

    installed_langgraph = package_version("langgraph")
    installed_checkpoint = package_version("langgraph-checkpoint")
    if installed_langgraph != LANGGRAPH_VERSION:
        raise RuntimeError(f"expected langgraph {LANGGRAPH_VERSION}, found {installed_langgraph}")
    if installed_checkpoint != LANGGRAPH_CHECKPOINT_VERSION:
        raise RuntimeError(
            f"expected langgraph-checkpoint {LANGGRAPH_CHECKPOINT_VERSION}, found {installed_checkpoint}"
        )

    substrate = InMemoryTemporalGraph()
    memory = GovernedMemoryAdapter(substrate, tenant=TENANT)
    replay_guard = MutationReplayGuard()
    seed = memory.commit_proposal(_seed_proposal(), "governed seed context")
    if not seed.committed:
        raise AssertionError("failed to seed governed LangGraph recall context")
    writes_after_seed = _write_count(substrate)

    saver = InMemorySaver()
    graph, nodes = _build_graph(memory, replay_guard, saver)

    allow_thread = "langgraph:thread:allow"
    allow_config = _thread_config(allow_thread)
    memory_state_before_allow = memory.state_version("mem:langgraph:lifecycle")
    allow_output = graph.invoke({"mode": "allow", "phase": "start"}, allow_config)
    writes_after_allow = _write_count(substrate)
    memory_state_after_allow = memory.state_version("mem:langgraph:lifecycle")
    if allow_output.get("status") != "committed":
        raise AssertionError(f"LangGraph allow path did not commit: {allow_output}")

    allow_history = _history(graph, allow_config)
    if not allow_history:
        raise AssertionError("LangGraph produced no checkpoint history for allow thread")
    latest_allow = graph.get_state(allow_config)
    latest_allow_id = _checkpoint_id(latest_allow.config)
    pre_mutation = _find_pre_mutation_snapshot(allow_history)
    pre_mutation_id = _checkpoint_id(pre_mutation.config)
    if latest_allow_id is None or pre_mutation_id is None:
        raise AssertionError("LangGraph checkpoint history lacked stable checkpoint IDs")
    lineage = _checkpoint_lineage(allow_history)
    pre_relation = classify_checkpoint_relation(pre_mutation_id, latest_allow_id, lineage)

    # The pre-mutation framework checkpoint is bound to Agent Memory state v0.
    # After the governed commit, that binding is stale even if framework lineage
    # is separately classified by LangGraph checkpoint ancestry.
    checkpoint_bound_memory_state = memory_state_before_allow
    checkpoint_memory_state_relation = (
        "current" if checkpoint_bound_memory_state == memory_state_after_allow else "stale"
    )

    state_before_replay = memory.state_version("mem:langgraph:lifecycle")
    writes_before_replay = _write_count(substrate)
    replay_output = graph.invoke(None, pre_mutation.config)
    state_after_replay = memory.state_version("mem:langgraph:lifecycle")
    writes_after_replay = _write_count(substrate)

    # Post-commit failure: the first retry-path mutation commits, records its
    # receipt, then raises. LangGraph RetryPolicy re-enters the node, where the
    # replay guard must reuse the original receipt instead of committing twice.
    retry_thread = "langgraph:thread:retry"
    retry_config = _thread_config(retry_thread)
    writes_before_retry = _write_count(substrate)
    retry_output = graph.invoke({"mode": "retry", "phase": "start"}, retry_config)
    writes_after_retry = _write_count(substrate)
    retry_state_version = memory.state_version("mem:langgraph:retry")
    retry_history = _history(graph, retry_config)

    deny_thread = "langgraph:thread:deny"
    deny_config = _thread_config(deny_thread)
    writes_before_deny = _write_count(substrate)
    deny_output = graph.invoke({"mode": "deny", "phase": "start"}, deny_config)
    writes_after_deny = _write_count(substrate)
    deny_history = _history(graph, deny_config)

    cross_scope_thread = "langgraph:thread:cross-scope"
    cross_scope_config = _thread_config(cross_scope_thread)
    cross_scope_output = graph.invoke({"mode": "cross_scope", "phase": "start"}, cross_scope_config)
    cross_scope_history = _history(graph, cross_scope_config)

    checkpoint_event = build_framework_lifecycle_event(
        framework_id="langgraph",
        framework_version=LANGGRAPH_VERSION,
        framework_source_ref=LANGGRAPH_SOURCE_REF,
        framework_source_commit=LANGGRAPH_COMMIT,
        event_type="checkpoint_saved",
        run_ref=allow_thread,
        workflow_ref=WORKFLOW_REF,
        persistence_classification="execution_state",
        occurred_at="2026-08-13T03:05:00Z",
        checkpoint_ref=pre_mutation_id,
        previous_checkpoint_ref=lineage.get(pre_mutation_id),
        checkpoint_relation=pre_relation,
        scope_ref=SCOPE,
        tenant_ref=TENANT,
        project_ref=PROJECT,
        memory_state_ref=f"v{checkpoint_bound_memory_state}",
        evidence_refs=("evidence:langgraph-checkpoint-history",),
    )
    commit_event = build_framework_lifecycle_event(
        framework_id="langgraph",
        framework_version=LANGGRAPH_VERSION,
        framework_source_ref=LANGGRAPH_SOURCE_REF,
        framework_source_commit=LANGGRAPH_COMMIT,
        event_type="mutation_committed",
        run_ref=allow_thread,
        workflow_ref=WORKFLOW_REF,
        persistence_classification="evidence",
        occurred_at="2026-08-13T03:05:01Z",
        action_ref="proposal:langgraph:allow-1",
        decision_receipt_ref=allow_output.get("receipt_ref"),
        scope_ref=SCOPE,
        tenant_ref=TENANT,
        project_ref=PROJECT,
        memory_state_ref=f"v{memory_state_after_allow}",
        idempotency_key="langgraph:allow:mutation-1",
        evidence_refs=(checkpoint_event["event_id"],),
    )
    retry_event = build_framework_lifecycle_event(
        framework_id="langgraph",
        framework_version=LANGGRAPH_VERSION,
        framework_source_ref=LANGGRAPH_SOURCE_REF,
        framework_source_commit=LANGGRAPH_COMMIT,
        event_type="retry",
        run_ref=retry_thread,
        workflow_ref=WORKFLOW_REF,
        persistence_classification="evidence",
        occurred_at="2026-08-13T03:05:02Z",
        action_ref="proposal:langgraph:retry-1",
        decision_receipt_ref=retry_output.get("receipt_ref"),
        scope_ref=SCOPE,
        tenant_ref=TENANT,
        project_ref=PROJECT,
        memory_state_ref=f"v{retry_state_version}",
        idempotency_key="langgraph:retry:mutation-1",
        evidence_refs=("evidence:langgraph-post-commit-retry",),
    )

    checks = {
        "real_langgraph_stategraph_executed": allow_output.get("phase") == "committed",
        "governed_recall_ran_in_graph": allow_output.get("recall_admitted") is True,
        "allowed_mutation_committed_once": writes_after_allow == writes_after_seed + 1,
        "allowed_memory_state_advanced_once": memory_state_before_allow == 0 and memory_state_after_allow == 1,
        "real_checkpoint_history_captured": len(allow_history) >= 2,
        "pre_mutation_checkpoint_identified": bool(pre_mutation_id),
        "framework_checkpoint_relation_explicit": pre_relation in {"stale", "divergent", "unknown", "current"},
        "pre_mutation_checkpoint_is_not_latest": pre_mutation_id != latest_allow_id,
        "checkpoint_bound_memory_state_becomes_stale": checkpoint_memory_state_relation == "stale",
        "old_checkpoint_replay_reused_receipt": (
            replay_output.get("status") == "replay"
            and replay_output.get("receipt_ref") == allow_output.get("receipt_ref")
        ),
        "old_checkpoint_replay_did_not_duplicate_write": writes_before_replay == writes_after_replay,
        "old_checkpoint_replay_did_not_rollback_memory": state_before_replay == state_after_replay == 1,
        "post_commit_retry_reused_receipt": retry_output.get("status") == "replay_after_retry",
        "post_commit_retry_committed_only_once": writes_after_retry == writes_before_retry + 1,
        "post_commit_retry_state_advanced_once": retry_state_version == 1,
        "retry_thread_has_checkpoint_history": bool(retry_history),
        "denied_mutation_remained_denied": deny_output.get("status") == "denied",
        "denied_mutation_did_not_write": writes_after_deny == writes_before_deny,
        "denied_thread_has_checkpoint_history": bool(deny_history),
        "valid_thread_did_not_widen_cross_scope_recall": cross_scope_output.get("recall_admitted") is False,
        "cross_scope_thread_has_checkpoint_history": bool(cross_scope_history),
        "framework_persistence_classified_execution_state": checkpoint_event["persistence_classification"] == "execution_state",
        "framework_persistence_not_memory_admission": checkpoint_event["interpretation"]["memory_admission"] == "not_established",
        "checkpoint_has_no_rollback_authority": checkpoint_event["interpretation"]["checkpoint_rollback_authority"] == "not_established",
        "same_generic_lifecycle_schema_used": (
            checkpoint_event["schema_version"] == commit_event["schema_version"] == retry_event["schema_version"] == "1.0.0"
        ),
        "trace_backend_optional": True,
    }
    passed = all(checks.values())
    result = {
        "schema_version": "1.0.0",
        "comparator": "langgraph-lifecycle-v0.1",
        "agent_memory_commit": agent_memory_commit,
        "pinned_framework": {
            "package": LANGGRAPH_PACKAGE,
            "tag": LANGGRAPH_TAG,
            "commit": LANGGRAPH_COMMIT,
            "installed_version": installed_langgraph,
            "checkpoint_package": LANGGRAPH_CHECKPOINT_PACKAGE,
            "installed_checkpoint_version": installed_checkpoint,
        },
        "runtime_identity": {
            "workflow_ref": WORKFLOW_REF,
            "allow_thread_ref": allow_thread,
            "retry_thread_ref": retry_thread,
            "deny_thread_ref": deny_thread,
            "cross_scope_thread_ref": cross_scope_thread,
        },
        "checkpoint_evidence": {
            "allow_history_count": len(allow_history),
            "pre_mutation_checkpoint": pre_mutation_id,
            "latest_after_allow": latest_allow_id,
            "framework_relation_after_allow": pre_relation,
            "checkpoint_bound_memory_state": checkpoint_bound_memory_state,
            "current_memory_state_after_allow": memory_state_after_allow,
            "checkpoint_memory_state_relation": checkpoint_memory_state_relation,
            "retry_history_count": len(retry_history),
            "deny_history_count": len(deny_history),
            "cross_scope_history_count": len(cross_scope_history),
        },
        "governance_evidence": {
            "committed_receipt_ref": allow_output.get("receipt_ref"),
            "replay_receipt_ref": replay_output.get("receipt_ref"),
            "retry_receipt_ref": retry_output.get("receipt_ref"),
            "denied_outcome": deny_output.get("decision_outcome"),
            "allow_state_version": state_after_replay,
            "retry_state_version": retry_state_version,
            "write_counts": {
                "after_seed": writes_after_seed,
                "after_allow": writes_after_allow,
                "before_replay": writes_before_replay,
                "after_replay": writes_after_replay,
                "before_retry": writes_before_retry,
                "after_retry": writes_after_retry,
                "before_deny": writes_before_deny,
                "after_deny": writes_after_deny,
            },
            "trace_correlation": "unavailable_not_authority",
        },
        "framework_lifecycle_events": [checkpoint_event, commit_event, retry_event],
        "checks": checks,
        "passed": passed,
        "non_claims": [
            "langgraph_checkpoint_is_not_memory_admission",
            "langgraph_thread_id_is_not_tenant_or_project_authority",
            "langgraph_persistence_is_not_memory_authority",
            "framework_checkpoint_recency_is_not_memory_state_freshness",
            "checkpoint_replay_has_no_memory_rollback_authority",
            "framework_retry_is_not_new_mutation_authority",
            "missing_trace_is_not_non_execution_evidence",
        ],
    }
    if not passed:
        failed = [name for name, ok in checks.items() if not ok]
        raise AssertionError(f"LangGraph lifecycle comparator failed: {failed}; result={result}")
    return result
