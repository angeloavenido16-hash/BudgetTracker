#!/usr/bin/env bash
# Restore backup SQLite DB and apply pending Alembic migrations.
set -euo pipefail

BACKUP="/tmp/budget_tracker_backup.db"
TARGET="backend/budget_tracker.db"

if [ ! -f "$BACKUP" ]; then
  echo "Error: backup not found at $BACKUP" >&2
  exit 1
fi

cp "$BACKUP" "$TARGET"
echo "→ Copied backup to $TARGET"

cd backend
.venv/bin/alembic stamp 0001_initial
.venv/bin/alembic upgrade head
echo "✓ Restore complete."
