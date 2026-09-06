use evolve_core::memory::types::{
    ContentType, InputMetadata, Query, QueryConstraints, RawInput, Sensitivity, Tier, TrustLevel,
};
use evolve_core::processor::facade::MemoryProcessor;
use evolve_core::processor::types::ProcessorConfig;
use evolve_core::representation::mock::MockEngine;
use evolve_core::shadow::interceptor::Verdict;
use evolve_core::shadow::types::{FailureCategory, FailureTrace};
use serde_json::json;

const DIMS: usize = 384;

fn raw(content: &str, sensitive: bool) -> RawInput {
    RawInput {
        content: content.to_string(),
        content_type: ContentType::Text,
        metadata: InputMetadata {
            tags: if sensitive {
                vec!["sensitive".to_string()]
            } else {
                Vec::new()
            },
            sensitivity: if sensitive {
                Sensitivity::Restricted
            } else {
                Sensitivity::Public
            },
            trust: TrustLevel::Verified,
            ..InputMetadata::default()
        },
    }
}

fn query(content: &str, tier: Option<Tier>) -> Query {
    Query {
        content: content.to_string(),
        constraints: QueryConstraints {
            require_tier: tier,
            top_k: Some(10),
            ..QueryConstraints::default()
        },
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut config = ProcessorConfig::default();
    config.lifecycle.synthesis_threshold = 3;
    let mut proc = MemoryProcessor::new(MockEngine::new(DIMS), config.clone());
    proc.start_session(1_000)?;

    let alpha = proc.encode(&raw("alpha memory", false), 1_100).await?;
    let beta = proc.encode(&raw("beta memory", false), 1_200).await?;
    let gamma = proc.encode(&raw("gamma memory", false), 1_300).await?;
    let l2_routing = [alpha.decision.tier, beta.decision.tier, gamma.decision.tier]
        .into_iter()
        .all(|tier| tier == Tier::L2);
    let temporal_graph_association = !proc.related(&alpha.unit.address).is_empty();

    let vector_result = proc.query(&query("alpha memory", None), 1_350).await?;
    let vector_scan_runtime = vector_result.recall.metrics.candidates_evaluated >= 3
        && !vector_result.recall.memories.is_empty();

    let detach = proc.detach(1_400)?;
    let lifecycle_synthesis = detach.synthesized && detach.traces_processed >= 3;

    proc.record_failure(
        FailureTrace {
            category: FailureCategory::Hallucination,
            severity: FailureCategory::Hallucination.default_severity(),
            intent: "danger-intent".to_string(),
            message: "qualification failure pattern".to_string(),
            timestamp: 1_450,
        },
        1_450,
    )
    .await?;
    let shadow_before = proc.shadow_stats();
    let shadow_verdict = proc.check_safety("danger-intent").await?;
    let shadow_candidate_block = matches!(shadow_verdict, Verdict::Block { .. })
        && shadow_before.total_entries == 1
        && shadow_before.active_entries == 1;

    let sensitive_content = "qualification sensitive durable memory";
    let sensitive = proc.encode(&raw(sensitive_content, true), 1_500).await?;
    let sensitive_address = sensitive.unit.address.clone();
    let l3_routing = sensitive.decision.tier == Tier::L3;

    let exact_before = proc
        .query(&query(sensitive_content, Some(Tier::L3)), 1_550)
        .await?;
    let exact_retrieval = exact_before.recall.metrics.candidates_evaluated == 1
        && exact_before.recall.memories.len() == 1
        && exact_before.recall.memories[0].unit.address == sensitive_address;

    let before_snapshot = proc.snapshot(1_600);
    let before_health = proc.health_check();
    let before_blocks = before_snapshot.l3_blocks.len();

    let state_path = std::env::temp_dir().join(format!(
        "agent-memory-evolveai-qualification-{}.json",
        std::process::id()
    ));
    proc.save_to_file(&state_path, 1_650)?;

    let mut restarted = MemoryProcessor::new(MockEngine::new(DIMS), config.clone());
    restarted.load_from_file(&state_path)?;
    let restart_snapshot = restarted.snapshot(1_700);
    let restart_result = restarted
        .query(&query(sensitive_content, Some(Tier::L3)), 1_750)
        .await?;
    let restart_preserved_current = restarted.health_check()
        && restart_snapshot.l3_blocks.len() == before_blocks
        && restart_result.recall.memories.len() == 1
        && restart_result.recall.memories[0].unit.address == sensitive_address;

    let deleted = restarted.forget(&sensitive_address);
    let after_delete = restarted.snapshot(1_800);
    let delete_payload = after_delete
        .l3_blocks
        .last()
        .map(|block| block.data_hash.clone())
        .unwrap_or_default();
    let audited_delete = deleted
        && restarted.health_check()
        && after_delete.l3_entries.is_empty()
        && delete_payload.starts_with(&format!("delete:{}:", sensitive_address));

    let post_delete_result = restarted
        .query(&query(sensitive_content, Some(Tier::L3)), 1_850)
        .await?;
    let deleted_not_current = post_delete_result.recall.memories.is_empty();

    restarted.save_to_file(&state_path, 1_900)?;
    let mut after_restart = MemoryProcessor::new(MockEngine::new(DIMS), config);
    after_restart.load_from_file(&state_path)?;
    let final_snapshot = after_restart.snapshot(1_950);
    let final_result = after_restart
        .query(&query(sensitive_content, Some(Tier::L3)), 2_000)
        .await?;
    let deletion_history_survives_restart = after_restart.health_check()
        && final_result.recall.memories.is_empty()
        && final_snapshot.l3_entries.is_empty()
        && final_snapshot
            .l3_blocks
            .last()
            .map(|block| block.data_hash.as_str())
            == Some(delete_payload.as_str());

    let _ = std::fs::remove_file(&state_path);

    let output = json!({
        "schema_version": "1.0.0",
        "provider": "evolveai",
        "provider_version": "21161ce7b88dbffeb7ed59757b4d02d24a9c2acd",
        "runtime": {
            "engine": "MockEngine",
            "dimensions": DIMS,
            "lifecycle_synthesis_threshold": 3,
            "real_embedding_path_exercised": false
        },
        "observations": {
            "l2_routing": l2_routing,
            "temporal_graph_association": temporal_graph_association,
            "vector_scan_runtime": vector_scan_runtime,
            "lifecycle_synthesis": lifecycle_synthesis,
            "shadow_candidate_block": shadow_candidate_block,
            "l3_routing": l3_routing,
            "exact_retrieval": exact_retrieval,
            "pre_restart_health": before_health,
            "restart_preserved_current": restart_preserved_current,
            "audited_delete": audited_delete,
            "deleted_not_current": deleted_not_current,
            "deletion_history_survives_restart": deletion_history_survives_restart
        },
        "native_evidence": {
            "sensitive_address": sensitive_address.as_str(),
            "l3_blocks_before_delete": before_blocks,
            "l3_blocks_after_delete": after_delete.l3_blocks.len(),
            "delete_payload": delete_payload,
            "shadow_total_entries": shadow_before.total_entries,
            "shadow_active_entries": shadow_before.active_entries,
            "detach_traces_processed": detach.traces_processed
        }
    });

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}
