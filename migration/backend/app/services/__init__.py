# services package
#
# - summaries: DB-agnostic financial formulas (parity-locked with desktop)
# - queries:   async SQLAlchemy fetch helpers that feed plain dict rows to them
from app.services import queries, summaries

__all__ = ["queries", "summaries"]
