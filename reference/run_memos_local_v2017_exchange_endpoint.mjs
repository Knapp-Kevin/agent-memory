#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const MEMOS_VERSION = "2.0.17";

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key?.startsWith("--") || value === undefined) throw new Error(`invalid argument near ${key}`);
    out[key.slice(2)] = value;
  }
  for (const required of ["action", "package-root", "home", "trace-id", "output"]) {
    if (!out[required]) throw new Error(`--${required} is required`);
  }
  if (!["write-read", "read"].includes(out.action)) throw new Error(`unsupported --action ${out.action}`);
  if (out.action === "write-read" && !out.content) throw new Error("--content is required for write-read");
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

async function main() {
  const args = parseArgs(process.argv);
  const packageJson = JSON.parse(await fs.readFile(path.join(args["package-root"], "package.json"), "utf8"));
  if (packageJson.name !== "@memtensor/memos-local-plugin" || packageJson.version !== MEMOS_VERSION) {
    throw new Error(`unexpected MemOS package identity ${packageJson.name}@${packageJson.version}`);
  }

  const coreUrl = pathToFileURL(path.join(args["package-root"], "dist", "core", "index.js")).href;
  const coreModule = await import(coreUrl);
  const { bootstrapMemoryCore, resolveConfig } = coreModule;
  if (typeof bootstrapMemoryCore !== "function" || typeof resolveConfig !== "function") {
    throw new Error("exact package does not expose bootstrapMemoryCore/resolveConfig");
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

  const core = await bootstrapMemoryCore({
    agent: "hermes",
    home,
    config,
    autoRecovery: false,
    pkgVersion: MEMOS_VERSION,
    initLogging: false,
  });

  let importResult = null;
  if (args.action === "write-read") {
    const trace = {
      id: args["trace-id"],
      episodeId: `${args["trace-id"]}:episode`,
      sessionId: `${args["trace-id"]}:session`,
      ts: 1735689600000,
      turnId: 1735689600000,
      userText: args.content,
      agentText: "federated exchange fixture",
      summary: args.content,
      toolCalls: [],
      reflection: null,
      agentThinking: null,
      value: 0,
      alpha: 0,
      rHuman: null,
      priority: 0,
      tags: ["agent-memory-federated-exchange"]
    };
    importResult = await core.importBundle({ version: 1, traces: [trace] });
  }

  const trace = await core.getTrace(args["trace-id"]);
  const count = await core.countTraces({ includeAllNamespaces: true });
  await core.shutdown();

  const result = {
    provider: {
      component_id: "memos-local-plugin-v2.0.17",
      component_version: MEMOS_VERSION,
      package: packageJson.name,
      package_version: packageJson.version,
      native_resource_id: args["trace-id"],
      runtime_ref: "memos-local-plugin:2.0.17:sqlite"
    },
    action: args.action,
    import_result: importResult,
    readback: trace?.userText ?? null,
    current_resource_count: count,
    native_id_matches: trace?.id === args["trace-id"],
    authority_effect: "none"
  };

  await fs.mkdir(path.dirname(path.resolve(args.output)), { recursive: true });
  await fs.writeFile(path.resolve(args.output), JSON.stringify(result, null, 2) + "\n", "utf8");
}

main().catch(async (err) => {
  const args = (() => { try { return parseArgs(process.argv); } catch { return {}; } })();
  if (args.output) {
    await fs.mkdir(path.dirname(path.resolve(args.output)), { recursive: true });
    await fs.writeFile(path.resolve(args.output), JSON.stringify({
      execution_error: err instanceof Error ? `${err.name}: ${err.message}` : String(err),
      authority_effect: "none"
    }, null, 2) + "\n", "utf8");
  }
  console.error(err);
  process.exitCode = 1;
});
