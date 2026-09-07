package agentmemory

import rego.v1

policy_revision := "agent-memory-opa-policy-v0.1.0"

# This policy is a comparator fixture, not canonical Agent Memory policy.
# It consumes only the minimized external-enforcement projection. A purpose
# marker chooses a deliberately stricter peer decision for the monotonic matrix;
# all other bounded cases return allow so native PAMA strictness remains visible.
decision := {
    "decision": "deny",
    "reason": "OPA comparator fixture denies the explicitly marked peer-deny case",
    "input_identity": input.input_identity,
    "policy_revision": policy_revision,
} if {
    input.purpose == "opa-deny"
} else := {
    "decision": "allow",
    "reason": "OPA comparator fixture allows this bounded projection",
    "input_identity": input.input_identity,
    "policy_revision": policy_revision,
}
