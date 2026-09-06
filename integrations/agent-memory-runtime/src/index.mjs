export const CONTRACT_VERSION = '0.1';
export const ADAPTER_NAME = 'agent-memory-runtime';
export const ADAPTER_VERSION = '0.1.1';

export class MemoryAdapterError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = 'MemoryAdapterError';
    this.code = code;
    this.details = details;
  }
}

function requireObject(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new MemoryAdapterError('invalid_handoff', `${name} must be an object`);
  }
  return value;
}

function requireString(value, name) {
  if (typeof value !== 'string' || value.trim().length === 0) {
    throw new MemoryAdapterError('invalid_handoff', `${name} must be a non-empty string`);
  }
  return value;
}

function requireStringArray(value, name, { minItems = 0 } = {}) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string' || item.length === 0)) {
    throw new MemoryAdapterError('invalid_handoff', `${name} must be an array of non-empty strings`);
  }
  if (value.length < minItems) {
    throw new MemoryAdapterError('invalid_handoff', `${name} must contain at least ${minItems} item(s)`);
  }
  return [...new Set(value)];
}

function normalizeScope(scope) {
  const input = requireObject(scope, 'scope');
  return Object.freeze({
    actor_id: requireString(input.actor_id, 'scope.actor_id'),
    project_id: requireString(input.project_id, 'scope.project_id'),
    task_id: requireString(input.task_id, 'scope.task_id'),
  });
}

function sameScope(left, right) {
  return Boolean(
    left && right
    && left.actor_id === right.actor_id
    && left.project_id === right.project_id
    && left.task_id === right.task_id,
  );
}

function normalizeSnapshot(snapshot) {
  const input = requireObject(snapshot, 'storage snapshot');
  return {
    revision: requireString(input.revision, 'storage snapshot.revision'),
    checkpoint: input.checkpoint == null ? null : requireString(input.checkpoint, 'storage snapshot.checkpoint'),
    records: Array.isArray(input.records) ? input.records : [],
  };
}

function assertStorage(storage) {
  const value = requireObject(storage, 'storage');
  for (const method of ['load', 'getCorrection', 'commitCorrection']) {
    if (typeof value[method] !== 'function') {
      throw new MemoryAdapterError('invalid_storage_port', `storage.${method} must be a function`);
    }
  }
  return value;
}

function nowIso(clock) {
  const value = clock();
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    throw new MemoryAdapterError('invalid_clock', 'clock must return a valid Date-compatible value');
  }
  return date.toISOString();
}

function defaultIdFactory(prefix) {
  if (globalThis.crypto?.randomUUID) return `${prefix}_${globalThis.crypto.randomUUID()}`;
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function recordScope(record) {
  if (!record || typeof record !== 'object' || Array.isArray(record)) return null;
  const scope = record.scope;
  if (!scope || typeof scope !== 'object' || Array.isArray(scope)) return null;
  if (![scope.actor_id, scope.project_id, scope.task_id].every((value) => typeof value === 'string' && value.length > 0)) {
    return null;
  }
  return scope;
}

function rejection(memoryId, reason) {
  return Object.freeze({ memory_id: memoryId ?? null, reason });
}

function admissionForRecord(record, scope, supersededIds) {
  if (!record || typeof record !== 'object' || Array.isArray(record)) {
    return { admitted: false, rejection: rejection(null, 'invalid_record') };
  }

  const memoryId = typeof record.memory_id === 'string' && record.memory_id.length > 0
    ? record.memory_id
    : null;
  if (!memoryId) return { admitted: false, rejection: rejection(null, 'missing_identity') };

  const scopeValue = recordScope(record);
  if (!scopeValue) return { admitted: false, rejection: rejection(memoryId, 'unknown_scope') };
  if (!sameScope(scopeValue, scope)) return { admitted: false, rejection: rejection(memoryId, 'out_of_scope') };
  if (record.state === 'disputed') return { admitted: false, rejection: rejection(memoryId, 'disputed') };
  if (record.state === 'superseded' || supersededIds.has(memoryId)) {
    return { admitted: false, rejection: rejection(memoryId, 'superseded') };
  }
  if (record.state && record.state !== 'active') {
    return { admitted: false, rejection: rejection(memoryId, `state_${record.state}`) };
  }

  return {
    admitted: true,
    value: Object.freeze({
      memory_id: memoryId,
      kind: requireString(record.kind ?? 'memory', `record ${memoryId}.kind`),
      value_ref: requireString(record.value_ref, `record ${memoryId}.value_ref`),
      scope: Object.freeze({ ...scopeValue }),
      state: 'active',
      evidence_refs: Array.isArray(record.evidence_refs) ? [...record.evidence_refs] : [],
      authority_refs: Array.isArray(record.authority_refs) ? [...record.authority_refs] : [],
      supersedes: Array.isArray(record.supersedes) ? [...record.supersedes] : [],
      created_at: record.created_at ?? null,
    }),
  };
}

function supersededSet(records) {
  const result = new Set();
  for (const record of records) {
    if (!record || typeof record !== 'object' || Array.isArray(record)) continue;
    if (!Array.isArray(record.supersedes)) continue;
    for (const id of record.supersedes) {
      if (typeof id === 'string' && id.length > 0) result.add(id);
    }
  }
  return result;
}

function normalizeRecallRequest(request) {
  const input = requireObject(request, 'recall request');
  return {
    scope: normalizeScope(input.scope),
    policy_version: requireString(input.policy_version, 'recall request.policy_version'),
    purpose: requireString(input.purpose, 'recall request.purpose'),
  };
}

function normalizeCorrectionRequest(request) {
  const input = requireObject(request, 'correction request');
  const replacement = requireObject(input.replacement, 'correction request.replacement');
  return {
    scope: normalizeScope(input.scope),
    memory_id: requireString(input.memory_id, 'correction request.memory_id'),
    idempotency_key: requireString(input.idempotency_key, 'correction request.idempotency_key'),
    policy_version: requireString(input.policy_version, 'correction request.policy_version'),
    evidence_refs: requireStringArray(input.evidence_refs, 'correction request.evidence_refs', { minItems: 1 }),
    authority_refs: requireStringArray(input.authority_refs, 'correction request.authority_refs', { minItems: 1 }),
    replacement: {
      kind: requireString(replacement.kind ?? 'correction', 'correction request.replacement.kind'),
      value_ref: requireString(replacement.value_ref, 'correction request.replacement.value_ref'),
    },
  };
}

function normalizeCommitRecord(raw) {
  const record = requireObject(raw, 'correction commit record');
  const replacement = requireObject(record.replacement, 'correction commit record.replacement');
  const event = requireObject(record.event, 'correction commit record.event');
  return Object.freeze({
    revision: requireString(record.revision, 'correction commit record.revision'),
    checkpoint: record.checkpoint == null
      ? null
      : requireString(record.checkpoint, 'correction commit record.checkpoint'),
    ledger_ref: requireString(record.ledger_ref, 'correction commit record.ledger_ref'),
    replacement: Object.freeze({ ...replacement }),
    event: Object.freeze({ ...event }),
    replayed: Boolean(record.replayed),
  });
}

function correctionReceipt(scope, rawCommit, replayedOverride) {
  const commit = normalizeCommitRecord(rawCommit);
  const replacementMemoryId = requireString(
    commit.replacement.memory_id,
    'correction commit record.replacement.memory_id',
  );
  const priorMemoryId = requireString(
    commit.event.prior_memory_id,
    'correction commit record.event.prior_memory_id',
  );
  const eventId = requireString(commit.event.event_id, 'correction commit record.event.event_id');
  const policyVersion = requireString(
    commit.event.policy_version,
    'correction commit record.event.policy_version',
  );
  const committedAt = requireString(
    commit.event.committed_at,
    'correction commit record.event.committed_at',
  );
  const authorityRefs = requireStringArray(
    commit.event.authority_refs,
    'correction commit record.event.authority_refs',
    { minItems: 1 },
  );
  const evidenceRefs = requireStringArray(
    commit.event.evidence_refs,
    'correction commit record.event.evidence_refs',
    { minItems: 1 },
  );

  return Object.freeze({
    contract_version: CONTRACT_VERSION,
    adapter: ADAPTER_NAME,
    adapter_version: ADAPTER_VERSION,
    scope,
    prior_memory_id: priorMemoryId,
    replacement_memory_id: replacementMemoryId,
    supersession: Object.freeze({
      prior_memory_id: priorMemoryId,
      replacement_memory_id: replacementMemoryId,
    }),
    event_id: eventId,
    revision: commit.revision,
    checkpoint: commit.checkpoint,
    ledger_ref: commit.ledger_ref,
    policy_version: policyVersion,
    authority_refs: Object.freeze(authorityRefs),
    evidence_refs: Object.freeze(evidenceRefs),
    replayed: replayedOverride ?? commit.replayed,
    committed_at: committedAt,
  });
}

export function createGovernedMemoryAdapter({
  storage,
  clock = () => new Date(),
  memoryIdFactory = () => defaultIdFactory('memory'),
  eventIdFactory = () => defaultIdFactory('memory_event'),
} = {}) {
  const persistence = assertStorage(storage);

  return Object.freeze({
    async recall(rawRequest) {
      const request = normalizeRecallRequest(rawRequest);
      const snapshot = normalizeSnapshot(await persistence.load(request.scope));
      const supersededIds = supersededSet(snapshot.records);
      const admitted = [];
      const rejected = [];

      for (const record of snapshot.records) {
        const admission = admissionForRecord(record, request.scope, supersededIds);
        if (admission.admitted) admitted.push(admission.value);
        else rejected.push(admission.rejection);
      }

      return Object.freeze({
        contract_version: CONTRACT_VERSION,
        adapter: ADAPTER_NAME,
        adapter_version: ADAPTER_VERSION,
        scope: request.scope,
        purpose: request.purpose,
        policy_version: request.policy_version,
        revision: snapshot.revision,
        checkpoint: snapshot.checkpoint,
        admitted: Object.freeze(admitted),
        rejected: Object.freeze(rejected),
        source_memory_refs: Object.freeze(admitted.map((record) => record.memory_id)),
        authority_effect: 'none',
        generated_at: nowIso(clock),
      });
    },

    async correct(rawRequest) {
      const request = normalizeCorrectionRequest(rawRequest);
      const replay = await persistence.getCorrection(request.scope, request.idempotency_key);
      if (replay) return correctionReceipt(request.scope, replay, true);

      const snapshot = normalizeSnapshot(await persistence.load(request.scope));
      const supersededIds = supersededSet(snapshot.records);
      const current = snapshot.records.find((record) => record?.memory_id === request.memory_id);

      if (!current) {
        throw new MemoryAdapterError('memory_not_found', 'The memory selected for correction does not exist', {
          memory_id: request.memory_id,
        });
      }
      const admission = admissionForRecord(current, request.scope, supersededIds);
      if (!admission.admitted) {
        throw new MemoryAdapterError('memory_not_current', 'Only a current in-scope memory can be corrected', {
          memory_id: request.memory_id,
          reason: admission.rejection.reason,
        });
      }

      const committedAt = nowIso(clock);
      const replacementMemoryId = requireString(memoryIdFactory(), 'memoryIdFactory result');
      const eventId = requireString(eventIdFactory(), 'eventIdFactory result');
      const replacement = Object.freeze({
        memory_id: replacementMemoryId,
        kind: request.replacement.kind,
        value_ref: request.replacement.value_ref,
        scope: request.scope,
        state: 'active',
        evidence_refs: request.evidence_refs,
        authority_refs: request.authority_refs,
        supersedes: [request.memory_id],
        created_at: committedAt,
      });
      const event = Object.freeze({
        event_id: eventId,
        event_type: 'correction_committed',
        prior_memory_id: request.memory_id,
        replacement_memory_id: replacementMemoryId,
        state_snapshot: snapshot.revision,
        policy_version: request.policy_version,
        evidence_refs: request.evidence_refs,
        authority_refs: request.authority_refs,
        committed_at: committedAt,
      });

      let committed;
      try {
        committed = await persistence.commitCorrection(request.scope, {
          idempotency_key: request.idempotency_key,
          expected_revision: snapshot.revision,
          replacement,
          event,
        });
      } catch (error) {
        if (error?.code === 'STALE_REVISION') {
          throw new MemoryAdapterError('stale_state', 'Memory state changed before the correction could commit', {
            expected_revision: snapshot.revision,
          });
        }
        throw error;
      }

      return correctionReceipt(request.scope, committed);
    },
  });
}
