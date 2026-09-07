@id("agent_memory_permit")
permit (
    principal,
    action,
    resource
);

@id("agent_memory_deny_purpose")
forbid (
    principal,
    action,
    resource
)
when {
    context.purpose == "cedar-deny"
};
