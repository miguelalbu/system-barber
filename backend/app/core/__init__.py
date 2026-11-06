"""
Infrastructure without business rules.

Package rule: nothing here imports `app.modules`, with one sanctioned exception —
`model_registry`, which must import every model so `Base.metadata` is complete
for Alembic (DEC-008). Enforced by import-linter (`pyproject.toml`).
"""
