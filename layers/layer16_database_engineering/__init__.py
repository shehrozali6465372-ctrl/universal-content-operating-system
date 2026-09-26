"""Layer 16 database-engineering contracts.

Layer 13 owns real PostgreSQL persistence. Layer 16 owns deterministic engineering
primitives: query construction, transactions, migrations, mapping, schema validation,
pooling, caching, repository/index metadata, snapshots, audit and recovery.
"""
__version__="16.1.1"
