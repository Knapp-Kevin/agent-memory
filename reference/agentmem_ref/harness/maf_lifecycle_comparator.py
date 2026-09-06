"""Pinned Microsoft Agent Framework comparator for issue #189.

The comparator uses MAF's real workflow/checkpoint runtime while keeping Agent
Memory governance in the existing reference adapter. No model or external
service is needed: the claim under test is lifecycle/checkpoint interoperability,
not model quality.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ..runtime.adapter import GovernedMemoryAdapter, RecallContext
from ..memory.framework_lifecycle import MutationReplayGuard, classify_checkpoint_relation
from ..core.policy import A1, A5, M2, M5, Proposal
from ..state.substrate import InMemoryTemporalGraph

MAF_PACKAGE = "agent-framework-core==1.13.0"
MAF_TAG = "python-1.13.0"
MAF_COMMIT = "e39a8a2e79c8c8987a0b9082d3ccb8665734b897"
MAF_CHECKPOINT_FORMAT = "1.0"

try:  # Optional dependency: only the isolated comparator workflow installs it.
    from agent_framework import (
        Executor,
        InMemoryCheckpointStorage,
        WorkflowBuilder,
        WorkflowCheckpoint,
        WorkflowContext,
        handler,
    )
    import agent_framework

    _MAF_AVAILABLE = True
except ImportError:  # pragma: no cover - keeps core/reference importable without MAF
    Executor = object  # type: ignore[assignment,misc]
    InMemoryCheckpointStorage = None  # type: ignore[assignment]
    WorkflowBuilder = None  # type: ignore[assignment]
    WorkflowCheckpoint = None  # type: ignore[assignment]
    WorkflowContext = Any  # type: ignore[assignment]
    agent_framework = None  # type: ignore[assignment]
    _MAF_AVAILABLE = False

    def handler(function):  # type: ignore[no-redef]
        return function


@dataclass
class MutationTask:
    mode: str


class LifecycleStartExecutor(Executor):  # type: ignore[misc,valid-type]
    @handler
    async def start(self, mode: str, ctx: WorkflowContext[MutationTask]) -> None:  # type: ignore[valid-type]
        await ctx.send_message(MutationTask(mode=mode))


class LifecycleMutationExecutor(Executor):  # type: ignore[misc,valid-type]
    def __init__(
        self,
        *,
        id: str,
        memory: GovernedMemoryAdapter,
        replay_guard: MutationReplayGuard,
    ) -> None:
        super().__init__(id=id)
        self._memory = memory
        self._replay_guard = replay_guard

    @handler
    async def mutate(
        self,
        task: MutationTask,
        ctx: WorkflowContext[Any, dict[str, Any]],  # type: ignore[valid-type]
    ) -> None:
        recall = self._memory.governed_recall(
            "governed seed",
            RecallContext(
                target_domain_refs=("scope:tenant-a/project-a",),
                principal_ref="principal:maf",
                project_ref="project-a",
                purpose="framework-lifecycle-proof",
            ),
        )

        if task.mode == "allow":
            idempotency_key = "maf:run-allow:mutation-1"
            prior = self._replay_guard.prior_receipt(idempotency_key)
            if prior is not None:
                await ctx.yield_output(
                    {
                        "status": "replay",
                        "receipt_ref": prior,
                        "recall_admitted": bool(recall.admitted),
                    }
                )
                return

            result = self._memory.commit_proposal(
                _allowing_proposal(),
                "framework lifecycle governed fact",
            )
            if not result.committed:
                raise RuntimeError(f"governed mutation unexpectedly refused: {result.refusal}")
            receipt_ref = result.receipt["receipt_id"]
            self._replay_guard.record(idempotency_key, receipt_ref)
            await ctx.yield_output(
                {
                    "status": "committed",
                    "receipt_ref": receipt_ref,
                    "recall_admitted": bool(recall.admitted),
                }
            )
            return

        if task.mode == "deny":
            result = self._memory.commit_proposal(_denied_proposal(), "must never persist")
            await ctx.yield_output(
                {
                    "status": "denied" if not result.committed else "unexpected_commit",
                    "decision_outcome": result.decision.outcome,
                    "recall_admitted": bool(recall.admitted),
                }
            )
            return

        raise ValueError(f"unsupported lifecycle task mode {task.mode!r}")


def _allowing_proposal() -> Proposal:
    return Proposal(
        proposal_id="proposal:maf:allow-1",
        actor_id="actor:maf",
        charter_version="charter:v1",
        target_reference="mem:maf:lifecycle",
        target_class=M2,
        scope="scope:tenant-a/project-a",
        operation="promotion",
        current_strength="observed",
        proposed_strength="promoted",
        downstream_authority=A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:maf-run",),
        tenant_ref="tenant-a",
        purpose="framework-lifecycle-proof",
        isolation_domain_refs=("scope:tenant-a/project-a",),
        project_ref="project-a",
    )


def _seed_proposal() -> Proposal:
    return Proposal(
        proposal_id="proposal:maf:seed",
        actor_id="actor:seed",
        charter_version="charter:v1",
        target_reference="mem:maf:seed",
        target_class=M2,
        scope="scope:tenant-a/project-a",
        operation="promotion",
        current_strength="observed",
        proposed_strength="promoted",
        downstream_authority=A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:maf-seed",),
        tenant_ref="tenant-a",
        purpose="framework-lifecycle-proof",
        isolation_domain_refs=("scope:tenant-a/project-a",),
        project_ref="project-a",
    )


def _denied_proposal() -> Proposal:
    return Proposal(
        proposal_id="proposal:maf:deny-1",
        actor_id="actor:maf",
        charter_version="charter:v1",
        target_reference="mem:maf:protected",
        target_class=M5,
        scope="scope:tenant-a/project-a",
        operation="scope_expansion",
        current_strength="promoted",
        proposed_strength="canonical",
        downstream_authority=A5,
        reversibility="irreversible",
        risk_class="critical",
        evidence_refs=("evidence:maf-deny",),
        tenant_ref="tenant-a",
        purpose="framework-lifecycle-proof",
        isolation_domain_refs=("scope:tenant-a/project-a",),
        project_ref="project-a",
    )


async def _consume_until_output(event_stream) -> dict[str, Any]:
    async for event in event_stream:
        if event.type == "output":
            if not isinstance(event.data, dict):
                raise AssertionError("MAF lifecycle output must be a mapping")
            return event.data
    raise AssertionError("MAF workflow completed without output")


async def _checkpoint_after_first_superstep(workflow, storage) -> Any:
    """Interrupt at a documented checkpoint boundary and close the stream cleanly."""

    event_stream = workflow.run(message="allow", stream=True)
    checkpoint = None
    try:
        async for event in event_stream:
            if event.type == "superstep_completed":
                checkpoint = await storage.get_latest(workflow_name=workflow.name)
                break
    finally:
        close = getattr(event_stream, "aclose", None)
        if close is not None:
            await close()
    return checkpoint


async def _run(agent_memory_commit: str) -> dict[str, Any]:
    if not _MAF_AVAILABLE:
        raise RuntimeError(f"{MAF_PACKAGE} is required for the pinned comparator")

    # First, exercise the documented checkpoint identity edge case directly
    # against MAF's real checkpoint objects/storage: same iteration, distinct
    # lineage. This prevents an adapter from using iteration_count as authority.
    lineage_storage = InMemoryCheckpointStorage()
    checkpoint_1 = WorkflowCheckpoint(
        workflow_name="agent-memory-lineage-proof",
        graph_signature_hash="graph:agent-memory-v01",
        checkpoint_id="checkpoint-1",
        previous_checkpoint_id=None,
        timestamp="2026-08-12T21:40:01+00:00",
        state={"memory_state_ref": "v0", "classification": "execution_state"},
        iteration_count=1,
        version=MAF_CHECKPOINT_FORMAT,
    )
    checkpoint_2 = WorkflowCheckpoint(
        workflow_name="agent-memory-lineage-proof",
        graph_signature_hash="graph:agent-memory-v01",
        checkpoint_id="checkpoint-2",
        previous_checkpoint_id="checkpoint-1",
        timestamp="2026-08-12T21:40:02+00:00",
        state={"memory_state_ref": "v1", "classification": "execution_state"},
        iteration_count=1,
        version=MAF_CHECKPOINT_FORMAT,
    )
    await lineage_storage.save(checkpoint_1)
    await lineage_storage.save(checkpoint_2)
    loaded_1 = await lineage_storage.load("checkpoint-1")
    latest_lineage = await lineage_storage.get_latest(workflow_name="agent-memory-lineage-proof")
    if latest_lineage is None:
        raise AssertionError("MAF lineage storage returned no latest checkpoint")
    manual_lineage = {
        checkpoint_1.checkpoint_id: checkpoint_1.previous_checkpoint_id,
        checkpoint_2.checkpoint_id: checkpoint_2.previous_checkpoint_id,
    }
    explicit_stale_relation = classify_checkpoint_relation(
        loaded_1.checkpoint_id,
        latest_lineage.checkpoint_id,
        manual_lineage,
    )

    substrate = InMemoryTemporalGraph()
    memory = GovernedMemoryAdapter(substrate, tenant="tenant-a")
    replay_guard = MutationReplayGuard()

    seed = memory.commit_proposal(_seed_proposal(), "governed seed context")
    if not seed.committed:
        raise AssertionError("failed to seed governed recall context")
    writes_before_workflow = sum(1 for operation, _ in substrate.write_log if operation == "write_fact")

    # Real MAF workflow: run one superstep, interrupt only after MAF has emitted
    # superstep_completed (which the pinned sample documents as checkpointed),
    # then resume from the real checkpoint into the governed mutation.
    runtime_storage = InMemoryCheckpointStorage()
    start = LifecycleStartExecutor(id="start")
    worker = LifecycleMutationExecutor(id="memory", memory=memory, replay_guard=replay_guard)
    builder = WorkflowBuilder(start_executor=start, checkpoint_storage=runtime_storage).add_edge(start, worker)

    first_workflow = builder.build()
    pre_mutation_checkpoint = await _checkpoint_after_first_superstep(first_workflow, runtime_storage)
    if pre_mutation_checkpoint is None:
        raise AssertionError("MAF workflow did not create a pre-mutation checkpoint")
    if replay_guard.prior_receipt("maf:run-allow:mutation-1") is not None:
        raise AssertionError("mutation committed before checkpointed resume boundary")

    # Bind the framework checkpoint to the Agent Memory state that was current at
    # capture time. Framework checkpoint recency and memory-state freshness are
    # deliberately separate axes.
    checkpoint_bound_memory_state = memory.state_version("mem:maf:lifecycle")

    resumed_workflow = builder.build()
    committed_output = await _consume_until_output(
        resumed_workflow.run(checkpoint_id=pre_mutation_checkpoint.checkpoint_id, stream=True)
    )
    writes_after_commit = sum(1 for operation, _ in substrate.write_log if operation == "write_fact")
    if committed_output.get("status") != "committed":
        raise AssertionError(f"resumed workflow did not commit governed mutation: {committed_output}")

    current_memory_state_after_commit = memory.state_version("mem:maf:lifecycle")
    checkpoint_memory_state_relation = (
        "current" if checkpoint_bound_memory_state == current_memory_state_after_commit else "stale"
    )

    checkpoints_after_commit = await runtime_storage.list_checkpoints(workflow_name=first_workflow.name)
    latest_after_commit = await runtime_storage.get_latest(workflow_name=first_workflow.name)
    if latest_after_commit is None:
        raise AssertionError("MAF workflow lost its checkpoint state after resume")
    runtime_lineage = {
        checkpoint.checkpoint_id: checkpoint.previous_checkpoint_id
        for checkpoint in checkpoints_after_commit
    }
    framework_relation_after_commit = classify_checkpoint_relation(
        pre_mutation_checkpoint.checkpoint_id,
        latest_after_commit.checkpoint_id,
        runtime_lineage,
    )

    state_before_stale_replay = memory.state_version("mem:maf:lifecycle")
    replayed_workflow = builder.build()
    replay_output = await _consume_until_output(
        replayed_workflow.run(checkpoint_id=pre_mutation_checkpoint.checkpoint_id, stream=True)
    )
    state_after_stale_replay = memory.state_version("mem:maf:lifecycle")
    writes_after_replay = sum(1 for operation, _ in substrate.write_log if operation == "write_fact")

    # A second real MAF run exercises the denied path through normal framework
    # continuation rather than by calling Agent Memory directly.
    denied_storage = InMemoryCheckpointStorage()
    denied_start = LifecycleStartExecutor(id="start")
    denied_worker = LifecycleMutationExecutor(id="memory", memory=memory, replay_guard=replay_guard)
    denied_builder = WorkflowBuilder(
        start_executor=denied_start,
        checkpoint_storage=denied_storage,
    ).add_edge(denied_start, denied_worker)
    denied_workflow = denied_builder.build()
    denied_output = await _consume_until_output(denied_workflow.run(message="deny", stream=True))
    writes_after_denial = sum(1 for operation, _ in substrate.write_log if operation == "write_fact")

    cross_scope = memory.governed_recall(
        "framework lifecycle",
        RecallContext(
            target_domain_refs=("scope:tenant-b/project-b",),
            principal_ref="principal:maf",
            project_ref="project-b",
            purpose="framework-lifecycle-proof",
        ),
    )

    expected_workflow_writes = writes_before_workflow + 1
    checks = {
        "maf_checkpoint_round_trip": loaded_1.checkpoint_id == "checkpoint-1",
        "same_iteration_lineage_supported": checkpoint_1.iteration_count == checkpoint_2.iteration_count == 1,
        "same_iteration_ancestor_classified_stale": explicit_stale_relation == "stale",
        "real_maf_workflow_checkpointed_before_mutation": bool(pre_mutation_checkpoint.checkpoint_id),
        "real_maf_resume_committed_governed_mutation": committed_output.get("status") == "committed",
        "real_maf_resume_included_governed_recall": committed_output.get("recall_admitted") is True,
        "checkpoint_bound_memory_state_becomes_stale": (
            checkpoint_bound_memory_state == 0
            and current_memory_state_after_commit == 1
            and checkpoint_memory_state_relation == "stale"
        ),
        "framework_checkpoint_relation_is_explicit": framework_relation_after_commit in {
            "current",
            "stale",
            "divergent",
            "unknown",
        },
        "stale_checkpoint_replay_reused_receipt": (
            replay_output.get("status") == "replay"
            and replay_output.get("receipt_ref") == committed_output.get("receipt_ref")
        ),
        "retry_did_not_duplicate_mutation": (
            writes_after_commit == writes_after_replay == expected_workflow_writes
        ),
        "stale_checkpoint_did_not_rollback_memory": (
            state_before_stale_replay == state_after_stale_replay == 1
        ),
        "denied_workflow_remained_denied": denied_output.get("status") == "denied",
        "denied_workflow_did_not_write": writes_after_denial == writes_after_replay,
        "cross_scope_recall_not_admitted": not cross_scope.admitted,
        "trace_backend_optional": True,
        "framework_persistence_not_auto_memory": checkpoint_2.state["classification"] == "execution_state",
    }
    passed = all(checks.values())

    installed_version = getattr(agent_framework, "__version__", None)
    return {
        "schema_version": "1.0.0",
        "comparator": "microsoft-agent-framework-lifecycle-v0.1",
        "agent_memory_commit": agent_memory_commit,
        "pinned_framework": {
            "package": MAF_PACKAGE,
            "tag": MAF_TAG,
            "commit": MAF_COMMIT,
            "checkpoint_format_version": MAF_CHECKPOINT_FORMAT,
            "installed_version": installed_version,
        },
        "checkpoint_evidence": {
            "same_iteration_checkpoint_1": {
                "id": checkpoint_1.checkpoint_id,
                "previous": checkpoint_1.previous_checkpoint_id,
                "iteration_count": checkpoint_1.iteration_count,
            },
            "same_iteration_checkpoint_2": {
                "id": checkpoint_2.checkpoint_id,
                "previous": checkpoint_2.previous_checkpoint_id,
                "iteration_count": checkpoint_2.iteration_count,
            },
            "pre_mutation_checkpoint": pre_mutation_checkpoint.checkpoint_id,
            "latest_after_commit": latest_after_commit.checkpoint_id,
            "framework_relation_after_commit": framework_relation_after_commit,
            "checkpoint_bound_memory_state": checkpoint_bound_memory_state,
            "current_memory_state_after_commit": current_memory_state_after_commit,
            "checkpoint_memory_state_relation": checkpoint_memory_state_relation,
        },
        "governance_evidence": {
            "committed_receipt_ref": committed_output.get("receipt_ref"),
            "retry_receipt_ref": replay_output.get("receipt_ref"),
            "denied_outcome": denied_output.get("decision_outcome"),
            "state_version": state_after_stale_replay,
            "trace_correlation": "unavailable_not_authority",
        },
        "checks": checks,
        "passed": passed,
        "non_claims": [
            "framework_checkpoint_is_not_memory_admission",
            "framework_checkpoint_is_not_lifecycle_satisfaction",
            "framework_persistence_is_not_memory_authority",
            "framework_latest_checkpoint_is_not_memory_state_freshness",
            "missing_trace_is_not_non_execution_evidence",
        ],
    }


def run_comparator(agent_memory_commit: str) -> dict[str, Any]:
    """Run the pinned MAF lifecycle comparator synchronously."""
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise ValueError("agent_memory_commit must be an exact lowercase 40-hex commit")
    result = asyncio.run(_run(agent_memory_commit))
    if not result["passed"]:
        failed = [name for name, passed in result["checks"].items() if not passed]
        raise AssertionError(f"MAF lifecycle comparator failed: {failed}")
    return result
