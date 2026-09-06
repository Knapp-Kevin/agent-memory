import assert from 'node:assert/strict';
import test from 'node:test';

import {
  MemoryAdapterError,
  createGovernedMemoryAdapter,
} from '../src/index.mjs';

const scope = Object.freeze({
  actor_id: 'actor:one',
  project_id: 'project:alpha',
  task_id: 'task:release-marker',
});

class InMemoryStorage {
  constructor(records = []) {
    this.records = structuredClone(records);
    this.revision = 'rev-1';
    this.checkpoint = 'checkpoint-1';
    this.corrections = new Map();
    this.events = [];
    this.failStale = false;
    this.raceCommit = null;
  }

  async load() {
    return {
      revision: this.revision,
      checkpoint: this.checkpoint,
      records: structuredClone(this.records),
    };
  }

  async getCorrection(_scope, key) {
    const record = this.corrections.get(key);
    return record ? structuredClone(record) : null;
  }

  async commitCorrection(_scope, transaction) {
    const existing = this.corrections.get(transaction.idempotency_key);
    if (existing) return { ...structuredClone(existing), replayed: true };
    if (this.raceCommit) return { ...structuredClone(this.raceCommit), replayed: true };

    if (this.failStale || transaction.expected_revision !== this.revision) {
      throw Object.assign(new Error('stale'), { code: 'STALE_REVISION' });
    }

    this.records.push(structuredClone(transaction.replacement));
    this.events.push(structuredClone(transaction.event));
    this.revision = `rev-${Number(this.revision.split('-')[1]) + 1}`;
    this.checkpoint = `checkpoint-${this.events.length + 1}`;

    const commitRecord = {
      revision: this.revision,
      checkpoint: this.checkpoint,
      ledger_ref: `ledger:${transaction.event.event_id}`,
      replacement: structuredClone(transaction.replacement),
      event: structuredClone(transaction.event),
      replayed: false,
    };
    this.corrections.set(transaction.idempotency_key, commitRecord);
    return structuredClone(commitRecord);
  }
}

function baseRecord(overrides = {}) {
  return {
    memory_id: 'memory-original',
    kind: 'fact',
    value_ref: 'value:staging',
    scope: structuredClone(scope),
    state: 'active',
    evidence_refs: ['evidence:seed'],
    authority_refs: [],
    supersedes: [],
    created_at: '2026-08-22T20:00:00.000Z',
    ...overrides,
  };
}

function adapter(storage) {
  let memoryCounter = 0;
  let eventCounter = 0;
  return createGovernedMemoryAdapter({
    storage,
    clock: () => new Date('2026-08-22T21:00:00.000Z'),
    memoryIdFactory: () => `memory-correction-${++memoryCounter}`,
    eventIdFactory: () => `event-correction-${++eventCounter}`,
  });
}

const recallRequest = {
  scope,
  policy_version: 'policy-v1',
  purpose: 'release_target_recall',
};

test('recall admits only exact-scope current memory and never grants authority', async () => {
  const storage = new InMemoryStorage([
    baseRecord(),
    baseRecord({
      memory_id: 'memory-foreign',
      scope: { ...scope, task_id: 'task:other' },
      value_ref: 'value:foreign',
    }),
    baseRecord({
      memory_id: 'memory-unknown-scope',
      scope: undefined,
      value_ref: 'value:unknown',
    }),
  ]);

  const result = await adapter(storage).recall(recallRequest);

  assert.deepEqual(result.source_memory_refs, ['memory-original']);
  assert.equal(result.admitted.length, 1);
  assert.equal(result.admitted[0].value_ref, 'value:staging');
  assert.equal(result.authority_effect, 'none');
  assert.equal('permitted_action_set' in result, false);
  assert.deepEqual(
    result.rejected.map((item) => item.reason).sort(),
    ['out_of_scope', 'unknown_scope'],
  );
});

test('superseded and disputed memory are rejected from active recall', async () => {
  const storage = new InMemoryStorage([
    baseRecord(),
    baseRecord({
      memory_id: 'memory-new',
      value_ref: 'value:main',
      supersedes: ['memory-original'],
    }),
    baseRecord({
      memory_id: 'memory-disputed',
      value_ref: 'value:disputed',
      state: 'disputed',
    }),
  ]);

  const result = await adapter(storage).recall(recallRequest);

  assert.deepEqual(result.source_memory_refs, ['memory-new']);
  assert.deepEqual(
    result.rejected.map((item) => [item.memory_id, item.reason]).sort(),
    [
      ['memory-disputed', 'disputed'],
      ['memory-original', 'superseded'],
    ],
  );
});

test('correction appends replacement and explicit supersession without erasing prior history', async () => {
  const storage = new InMemoryStorage([baseRecord()]);
  const governed = adapter(storage);

  const receipt = await governed.correct({
    scope,
    memory_id: 'memory-original',
    idempotency_key: 'correction:one',
    policy_version: 'policy-v1',
    evidence_refs: ['evidence:user-correction'],
    authority_refs: ['authority:human-confirmed'],
    replacement: {
      kind: 'correction',
      value_ref: 'value:main',
    },
  });

  assert.equal(receipt.adapter_version, '0.1.1');
  assert.equal(receipt.prior_memory_id, 'memory-original');
  assert.equal(receipt.replacement_memory_id, 'memory-correction-1');
  assert.equal(storage.records.length, 2);
  assert.equal(storage.records[0].memory_id, 'memory-original');
  assert.deepEqual(storage.records[1].supersedes, ['memory-original']);
  assert.equal(storage.events.length, 1);
  assert.equal(storage.events[0].event_type, 'correction_committed');

  const persisted = storage.corrections.get('correction:one');
  assert.deepEqual(
    Object.keys(persisted).sort(),
    ['checkpoint', 'event', 'ledger_ref', 'replacement', 'replayed', 'revision'],
  );
  assert.equal('contract_version' in persisted, false);
  assert.equal('supersession' in persisted, false);

  const recalled = await governed.recall(recallRequest);
  assert.deepEqual(recalled.source_memory_refs, ['memory-correction-1']);
});

test('idempotent correction replay reconstructs the original semantic receipt in Agent Memory', async () => {
  const storage = new InMemoryStorage([baseRecord()]);
  const governed = adapter(storage);
  const request = {
    scope,
    memory_id: 'memory-original',
    idempotency_key: 'correction:one',
    policy_version: 'policy-v1',
    evidence_refs: ['evidence:user-correction'],
    authority_refs: ['authority:human-confirmed'],
    replacement: { value_ref: 'value:main' },
  };

  const first = await governed.correct(request);
  const second = await governed.correct(request);

  assert.equal(first.replacement_memory_id, second.replacement_memory_id);
  assert.equal(first.event_id, second.event_id);
  assert.equal(first.committed_at, second.committed_at);
  assert.equal(first.ledger_ref, second.ledger_ref);
  assert.equal(first.replayed, false);
  assert.equal(second.replayed, true);
  assert.equal(storage.records.length, 2);
  assert.equal(storage.events.length, 1);
});

test('commit-time idempotency race returns the original persisted transaction instead of candidate identities', async () => {
  const storage = new InMemoryStorage([baseRecord()]);
  storage.raceCommit = {
    revision: 'rev-2',
    checkpoint: 'checkpoint-2',
    ledger_ref: 'ledger:event-existing',
    replacement: {
      memory_id: 'memory-existing',
      kind: 'correction',
      value_ref: 'value:main',
      scope,
      state: 'active',
      evidence_refs: ['evidence:user-correction'],
      authority_refs: ['authority:human-confirmed'],
      supersedes: ['memory-original'],
      created_at: '2026-08-22T20:59:59.000Z',
    },
    event: {
      event_id: 'event-existing',
      event_type: 'correction_committed',
      prior_memory_id: 'memory-original',
      replacement_memory_id: 'memory-existing',
      state_snapshot: 'rev-1',
      policy_version: 'policy-v1',
      evidence_refs: ['evidence:user-correction'],
      authority_refs: ['authority:human-confirmed'],
      committed_at: '2026-08-22T20:59:59.000Z',
    },
    replayed: false,
  };

  const receipt = await adapter(storage).correct({
    scope,
    memory_id: 'memory-original',
    idempotency_key: 'correction:race',
    policy_version: 'policy-v1',
    evidence_refs: ['evidence:user-correction'],
    authority_refs: ['authority:human-confirmed'],
    replacement: { value_ref: 'value:main' },
  });

  assert.equal(receipt.replacement_memory_id, 'memory-existing');
  assert.equal(receipt.event_id, 'event-existing');
  assert.equal(receipt.committed_at, '2026-08-22T20:59:59.000Z');
  assert.equal(receipt.replayed, true);
  assert.equal(storage.records.length, 1);
  assert.equal(storage.events.length, 0);
});

test('correction requires explicit authority and evidence', async () => {
  const storage = new InMemoryStorage([baseRecord()]);
  const governed = adapter(storage);

  await assert.rejects(
    governed.correct({
      scope,
      memory_id: 'memory-original',
      idempotency_key: 'correction:no-authority',
      policy_version: 'policy-v1',
      evidence_refs: ['evidence:user-correction'],
      authority_refs: [],
      replacement: { value_ref: 'value:main' },
    }),
    (error) => error instanceof MemoryAdapterError && error.code === 'invalid_handoff',
  );
  assert.equal(storage.records.length, 1);
});

test('stale state fails closed instead of committing against an old snapshot', async () => {
  const storage = new InMemoryStorage([baseRecord()]);
  storage.failStale = true;

  await assert.rejects(
    adapter(storage).correct({
      scope,
      memory_id: 'memory-original',
      idempotency_key: 'correction:stale',
      policy_version: 'policy-v1',
      evidence_refs: ['evidence:user-correction'],
      authority_refs: ['authority:human-confirmed'],
      replacement: { value_ref: 'value:main' },
    }),
    (error) => error instanceof MemoryAdapterError && error.code === 'stale_state',
  );
  assert.equal(storage.records.length, 1);
});

test('invalid scope is rejected before storage can launder it into local context', async () => {
  let loaded = false;
  const storage = new InMemoryStorage([baseRecord()]);
  storage.load = async () => {
    loaded = true;
    return { revision: 'rev-1', checkpoint: null, records: [] };
  };

  await assert.rejects(
    adapter(storage).recall({
      scope: { actor_id: 'actor:one', project_id: 'project:alpha', task_id: '' },
      policy_version: 'policy-v1',
      purpose: 'test',
    }),
    (error) => error instanceof MemoryAdapterError && error.code === 'invalid_handoff',
  );
  assert.equal(loaded, false);
});
