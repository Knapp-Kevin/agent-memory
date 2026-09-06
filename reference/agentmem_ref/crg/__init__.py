"""Agent Memory's Code Reality Graph.

A Code Reality Graph is a governed graph of what a codebase actually is --
its structure, its qualified components, its scope residue -- held as memory
the PAMA evaluator governs like any other. CodeGenome is the first-party
implementation profile of that graph (ADR-035, ADR-036); the ``codegenome_*``
modules here are that profile, not an attributed external provider.
Depends on ``memory`` and below.
"""
