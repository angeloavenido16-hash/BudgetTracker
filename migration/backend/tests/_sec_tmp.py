import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path("migration/backend").resolve()))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["APP_USERNAME"] = "admin"
# A long password (>72 bytes) to exercise bcrypt's 72-byte limit handling.
os.environ["APP_PASSWORD"] = "p" * 100

from jose import jwt  # noqa: E402

from app import security  # noqa: E402
from app.config import settings  # noqa: E402

issues = []

# 1) Correct long password verifies (no ValueError from bcrypt 72-byte limit).
if not security.verify_credentials("admin", "p" * 100):
    issues.append("long password should verify")

# 2) Wrong password rejected.
if security.verify_credentials("admin", "wrong"):
    issues.append("wrong password should NOT verify")

# 3) Wrong username rejected.
if security.verify_credentials("nope", "p" * 100):
    issues.append("wrong username should NOT verify")

# 4) A token with no 'sub' must be rejected by get_current_user.
import asyncio  # noqa: E402

bad = jwt.encode({"foo": "bar"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
try:
    asyncio.run(security.get_current_user(bad))
    issues.append("token without sub should raise 401")
except Exception as ex:  # noqa: BLE001
    if ex.__class__.__name__ != "HTTPException":
        issues.append(f"unexpected error type for no-sub token: {ex!r}")

# 5) A valid token round-trips to the username.
good = security.create_access_token("admin")
who = asyncio.run(security.get_current_user(good))
if who != "admin":
    issues.append(f"valid token should return 'admin', got {who!r}")

if issues:
    print("ISSUES:")
    for i in issues:
        print("  -", i)
    sys.exit(1)
print("SECURITY EDGE CASES: ALL OK")
