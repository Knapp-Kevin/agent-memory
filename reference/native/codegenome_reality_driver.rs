use std::collections::HashSet;
use std::path::Path;

use codegenome_identity::graph::edge::{Edge, Relation};
use codegenome_identity::graph::node::Node;
use codegenome_identity::graph::overlay::OverlayKind;
use codegenome_identity::graph::query::Query;
use codegenome_identity::graph::query_context::LocalQueryContext;
use codegenome_identity::graph::traversal;
use codegenome_identity::identity::{address_of, UorAddress};
use codegenome_identity::store::backend::StoreBackend;
use codegenome_identity::store::meta;
use codegenome_identity::store::ondisk::OnDiskStore;
use serde_json::json;

const PROVIDER_VERSION: &str = "43a6b7147ec78ec5c616723fa1dd30f342174860";

fn normalize_path(value: &str) -> String {
    let normalized = value.replace('\\', "/");
    normalized
        .strip_prefix("./")
        .unwrap_or(&normalized)
        .trim_end_matches('/')
        .to_string()
}

fn resolve_indexed_file(store_dir: &Path, requested_file: &str) -> Result<String, String> {
    let index = meta::load(store_dir)?
        .ok_or_else(|| format!("no index metadata found at {}", store_dir.display()))?;
    let requested = normalize_path(requested_file);
    let mut exact = Vec::new();
    let mut suffix = Vec::new();
    for indexed in index.source_hashes.keys() {
        let normalized = normalize_path(indexed);
        if normalized == requested {
            exact.push(indexed.clone());
        } else if normalized.ends_with(&format!("/{requested}")) {
            suffix.push(indexed.clone());
        }
    }
    let matches = if exact.is_empty() { suffix } else { exact };
    match matches.as_slice() {
        [only] => Ok(only.clone()),
        [] => Err(format!("file is not present in the index: {requested_file}")),
        many => Err(format!("file path is ambiguous across {} indexed sources", many.len())),
    }
}

fn find_node_at(nodes: &[Node], edges: &[Edge], indexed_file: &str, line: u32) -> Result<UorAddress, String> {
    let file_addr = address_of(format!("file:{indexed_file}").as_bytes());
    let contained: HashSet<UorAddress> = edges
        .iter()
        .filter(|edge| edge.source == file_addr && edge.relation == Relation::Contains)
        .map(|edge| edge.target)
        .collect();
    let mut candidates: Vec<&Node> = nodes
        .iter()
        .filter(|node| contained.contains(&node.address))
        .filter(|node| {
            node.span
                .as_ref()
                .is_some_and(|span| span.start_line <= line && span.end_line >= line)
        })
        .collect();
    if candidates.is_empty() {
        return Err(format!("no symbol found at {indexed_file}:{line}"));
    }
    candidates.sort_by_key(|node| {
        node.span
            .as_ref()
            .map(|span| span.end_line.saturating_sub(span.start_line))
            .unwrap_or(u32::MAX)
    });
    let best_width = candidates[0]
        .span
        .as_ref()
        .map(|span| span.end_line.saturating_sub(span.start_line))
        .unwrap_or(u32::MAX);
    let best: Vec<&Node> = candidates
        .into_iter()
        .take_while(|node| {
            node.span
                .as_ref()
                .map(|span| span.end_line.saturating_sub(span.start_line))
                .unwrap_or(u32::MAX)
                == best_width
        })
        .collect();
    match best.as_slice() {
        [only] => Ok(only.address),
        many => Err(format!("{} equally specific symbols contain line {line}", many.len())),
    }
}

fn source_name(value: &codegenome_identity::graph::node::Source) -> String {
    format!("{value:?}")
}

fn main() -> Result<(), String> {
    let mut args = std::env::args().skip(1);
    let store_dir = args.next().ok_or("usage: driver <store-dir> <file> <line>")?;
    let file = args.next().ok_or("missing file")?;
    let line: u32 = args
        .next()
        .ok_or("missing line")?
        .parse()
        .map_err(|_| "line must be an integer")?;

    let store = OnDiskStore::new(&store_dir);
    let (nodes, edges) = store
        .read_overlay(&OverlayKind::Custom("fused".into()))
        .map_err(|error| error.to_string())?
        .ok_or("fused overlay unavailable")?;
    let indexed_file = resolve_indexed_file(Path::new(&store_dir), &file)?;
    let target = find_node_at(&nodes, &edges, &indexed_file, line)?;

    let ctx = LocalQueryContext::new(&nodes, &edges);
    let result = traversal::execute(&Query::downstream(target, 2), &ctx);
    let relation = result
        .edges
        .iter()
        .find(|edge| edge.source == target && edge.relation == Relation::Calls)
        .ok_or("native downstream traversal produced no direct Calls relation")?;
    let target_node = nodes
        .iter()
        .find(|node| node.address == target)
        .ok_or("target node missing from fused overlay")?;

    let payload = json!({
        "schema_version": "1.0.0",
        "provider": "codegenome",
        "provider_version": PROVIDER_VERSION,
        "operation": "code_graph_traversal",
        "query": {
            "file": file,
            "line": line,
            "direction": "downstream",
            "max_depth": 2,
            "native_result_confidence": result.confidence,
            "path_count": result.paths.len(),
            "edge_count": result.edges.len()
        },
        "target": {
            "uor": target.to_string(),
            "kind": format!("{:?}", target_node.kind),
            "confidence": target_node.confidence,
            "content_hash": target_node.content_hash.to_string()
        },
        "relation": {
            "source_uor": relation.source.to_string(),
            "target_uor": relation.target.to_string(),
            "kind": format!("{:?}", relation.relation),
            "confidence": relation.confidence,
            "provenance": {
                "source": source_name(&relation.provenance.source),
                "actor": relation.provenance.actor,
                "timestamp_ms": relation.provenance.timestamp.0,
                "justification_uor": relation.provenance.justification.map(|value| value.to_string())
            },
            "evidence": relation.evidence.iter().map(ToString::to_string).collect::<Vec<_>>()
        }
    });
    println!("{}", serde_json::to_string_pretty(&payload).map_err(|error| error.to_string())?);
    Ok(())
}
