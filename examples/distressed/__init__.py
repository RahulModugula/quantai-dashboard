"""Distressed-credit worked examples.

Re-uses the QuantAI agent orchestration pattern for bankruptcy / restructuring
situations. Not a complete distressed-credit platform — a proof of concept that
the debate loop is asset-class-agnostic.

Shared data types (CapitalStructureTranche, Situation, helpers) live in models.py
to avoid circular imports between agents.py and credit_tools.py.
"""
