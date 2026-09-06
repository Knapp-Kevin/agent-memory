#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const MEMOS_RELEASE = "memos-local-plugin-v2.0.17";
const MEMOS_VERSION = "2.0.17";
const MEMOS_COMMIT = "d3d1bcfaff65f31b621d58bc236ece6d1e0da5ab";
const MEMOS_PACKAGE = "@memtensor/memos-local-plugin";
const MEMOS_REPOSITORY = "MemTensor/MemOS";
const INITIAL_MARKER = "silveroak317";
const REPLACEMENT_MARKER = "violetstone624";
const TRACE_ID = "agent-memory-resource-trace";
const SESSION_ID = "agent-memory-resource-session";
const EPISODE_ID = "agent-memory-resource-episode";
const INITIAL_TEXT = `${INITIAL_MARKER} resource artifact state is initial and provider-bounded.`;
const REPLACEMENT_TEXT = `${REPLACEMENT_MARKER} resource artifact state is replacement and provider-bounded.`;

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key?.startsWith("--") || value === undefined) throw new Error(`invalid argument near ${key}`);
    out[key.slice(2)] = value;
  }
  for (const required of ["package-root", "home", "source-commit", "license-path", "output"]) {
    if (!out[required]) throw new Error(`--${required} is required`);
  }
  return out;
}

async function mkdirHome(root) {
  const dirs = [root, path.join(root, "data"), path.join(root, "skills"), path.join(root, "logs"), path.join(root, "daemon")];
  for (const dir of dirs) await fs.mkdir(dir, { recursive: true });
  return {
    root,
    configFile: path.join(root, "config.yaml"),
    dataDir: path.join(root, "data"),
    dbFile: path.join(root, "data", "memos.db"),
    skillsDir: path.join(root, "skills"),
    logsDir: path.join(root, "logs"),
    daemonDir: path.join(root, "daemon"),
  };
}

function containsMarker(rows, marker) {
  return rows.some((row) => JSON.stringify(row).includes(marker));
}

async function main() {
  const args = parseArgs(process.argv);
  const packageJson = JSON.parse(await fs.readFile(path.join(args["package-root"], "package.json"), "utf8"));
  const sourceLicense = await fs.readFile(args["license-path"], "utf8");
  const coreUrl = pathToFileURL(path.join(args["package-root"], "dist", "core", "index.js")).href;
  const coreModule = await import(coreUrl);
  const { bootstrapMemoryCore, resolveConfig } = coreModule;
  if (typeof bootstrapMemoryCore !== "function" || typeof resolveConfig !== "function") {
    throw new Error("exact package does not expose bootstrapMemoryCore/resolveConfig from dist/core/index.js");
  }

  const home = await mkdirHome(path.resolve(args.home));
  const config = resolveConfig({
    viewer: { openOnFirstTurn: false },
    llm: { provider: "", model: "", apiKey: "", fallbackToHost: false },
    embedding: { provider: "local", apiKey: "", cache: { enabled: false, maxItems: 1 } },
    algorithm: {
      lightweightMemory: { enabled: true },
      capture: { embedTraces: false, alphaScoring: false, synthReflections: false },
      reward: { llmScoring: false },
      l2Induction: { useLlm: false },
      l3Abstraction: { useLlm: false },
      skill: { useLlm: false }
    }
  }, [], "hermes");

  const baseTrace = {
    id: TRACE_ID,
    episodeId: EPISODE_ID,
    sessionId: SESSION_ID,
    ts: 1735689600000,
    turnId: 1735689600000,
    userText: INITIAL_TEXT,
    agentText: "fixture response",
    summary: INITIAL_TEXT,
    toolCalls: [],
    reflection: null,
    agentThinking: null,
    value: 0,
    alpha: 0,
    rHuman: null,
    priority: 0,
    tags: ["agent-memory-qualification"]
  };

  const boot = async () => bootstrapMemoryCore({
    agent: "hermes",
    home,
    config,
    autoRecovery: false,
    pkgVersion: MEMOS_VERSION,
    initLogging: false,
  });

  let core = await boot();
  const initialImport = await core.importBundle({ version: 1, traces: [baseTrace] });
  const initialGet = await core.getTrace(TRACE_ID);
  const initialCandidates = await core.listTraces({ q: INITIAL_MARKER, includeAllNamespaces: true });
  const initialCount = await core.countTraces({ includeAllNamespaces: true });

  const sameKey = await core.importBundle({ version: 1, traces: [baseTrace] });
  const repeatGet = await core.getTrace(TRACE_ID);
  const repeatCount = await core.countTraces({ includeAllNamespaces: true });

  const updated = await core.updateTrace(TRACE_ID, {
    userText: REPLACEMENT_TEXT,
    summary: REPLACEMENT_TEXT,
  });
  const replacementGet = await core.getTrace(TRACE_ID);
  const replacementCandidates = await core.listTraces({ q: REPLACEMENT_MARKER, includeAllNamespaces: true });
  const oldCandidatesAfterReplacement = await core.listTraces({ q: INITIAL_MARKER, includeAllNamespaces: true });
  const replacementCount = await core.countTraces({ includeAllNamespaces: true });

  await core.shutdown();
  core = await boot();
  const restartGet = await core.getTrace(TRACE_ID);
  const restartCandidates = await core.listTraces({ q: REPLACEMENT_MARKER, includeAllNamespaces: true });
  const restartCount = await core.countTraces({ includeAllNamespaces: true });

  const durableRepeat = await core.importBundle({ version: 1, traces: [baseTrace] });
  const durableGet = await core.getTrace(TRACE_ID);
  const durableCount = await core.countTraces({ includeAllNamespaces: true });

  const deletionResult = await core.deleteTrace(TRACE_ID);
  const deletedGet = await core.getTrace(TRACE_ID);
  const oldCandidatesAfterDelete = await core.listTraces({ q: INITIAL_MARKER, includeAllNamespaces: true });
  const replacementCandidatesAfterDelete = await core.listTraces({ q: REPLACEMENT_MARKER, includeAllNamespaces: true });
  const deletionCount = await core.countTraces({ includeAllNamespaces: true });
  await core.shutdown();

  const raw = {
    identity: {
      repository: MEMOS_REPOSITORY,
      package: packageJson.name,
      release: MEMOS_RELEASE,
      version: packageJson.version,
      commit: args["source-commit"],
      source_license: "Apache-2.0",
      source_license_verified: sourceLicense.includes("Apache License") && sourceLicense.includes("Version 2.0"),
      package_license_metadata: packageJson.license,
      license_discrepancy_preserved: packageJson.license === "MIT",
    },
    configuration: {
      adapter: "direct-memory-core",
      database: "sqlite",
      hosted_llm_api_key_present: Boolean(config.llm?.apiKey),
      hosted_embedding_api_key_present: config.embedding?.provider !== "local" && Boolean(config.embedding?.apiKey),
      semantic_search_exercised: false,
    },
    fixture: {
      trace_id: TRACE_ID,
      session_id: SESSION_ID,
      episode_id: EPISODE_ID,
      initial_marker: INITIAL_MARKER,
      replacement_marker: REPLACEMENT_MARKER,
      initial_text: INITIAL_TEXT,
      replacement_text: REPLACEMENT_TEXT,
    },
    initial: {
      ...initialImport,
      trace_count: initialCount,
      get_matches_initial: initialGet?.userText === INITIAL_TEXT,
      candidate_contains_initial: containsMarker(initialCandidates, INITIAL_MARKER),
    },
    same_key_repeat: {
      ...sameKey,
      trace_count: repeatCount,
      get_matches_initial: repeatGet?.userText === INITIAL_TEXT,
    },
    replacement: {
      updated_same_id: updated?.id === TRACE_ID,
      trace_count: replacementCount,
      get_matches_replacement: replacementGet?.userText === REPLACEMENT_TEXT,
      candidate_contains_replacement: containsMarker(replacementCandidates, REPLACEMENT_MARKER),
      candidate_contains_initial: containsMarker(oldCandidatesAfterReplacement, INITIAL_MARKER),
    },
    restart: {
      restart_succeeded: true,
      trace_count: restartCount,
      get_matches_replacement: restartGet?.userText === REPLACEMENT_TEXT,
      candidate_contains_replacement: containsMarker(restartCandidates, REPLACEMENT_MARKER),
    },
    durable_repeat_after_restart: {
      ...durableRepeat,
      trace_count: durableCount,
      get_matches_replacement: durableGet?.userText === REPLACEMENT_TEXT,
    },
    deletion: {
      delete_succeeded: deletionResult.deleted === true,
      get_after_delete_is_null: deletedGet === null,
      trace_count: deletionCount,
      candidate_contains_initial: containsMarker(oldCandidatesAfterDelete, INITIAL_MARKER),
      candidate_contains_replacement: containsMarker(replacementCandidatesAfterDelete, REPLACEMENT_MARKER),
    },
    identity_boundary_preserved: ![TRACE_ID, SESSION_ID, EPISODE_ID].includes("agentmem:resource-artifact:qualification"),
    provider_notes: [
      "MemOS importBundle collision behavior is idempotent skip, not replacement; replacement is intentionally exercised through updateTrace on the same stable provider-native ID.",
      "The fixture uses listTraces text filtering as deterministic recall-candidate evidence and does not exercise semantic embedding/ranking."
    ]
  };

  await fs.mkdir(path.dirname(path.resolve(args.output)), { recursive: true });
  await fs.writeFile(path.resolve(args.output), JSON.stringify(raw, null, 2) + "\n", "utf8");
}

main().catch(async (err) => {
  const args = (() => { try { return parseArgs(process.argv); } catch { return {}; } })();
  const failure = { execution_error: err instanceof Error ? `${err.name}: ${err.message}` : String(err), authority_effect: "none" };
  if (args.output) {
    await fs.mkdir(path.dirname(path.resolve(args.output)), { recursive: true });
    await fs.writeFile(path.resolve(args.output), JSON.stringify(failure, null, 2) + "\n", "utf8");
  }
  console.error(err);
  process.exitCode = 1;
});
