"""
tests/test_api_endpoints.py
───────────────────────────
End-to-end API tests for the Phase 2 routers.

Boots the real FastAPI app against an in-memory SQLite DB (aiosqlite), overrides
get_session, creates the schema from the ORM metadata, then drives the entire
API surface through httpx's ASGI transport:

  auth → funds CRUD → transactions CRUD → categories → bpi → dashboard → reports

This verifies the parity-locked formulas surface correctly through the router +
schema layers, plus auth gating, validation errors, and FK cascade on delete.

Run with pytest (in the backend venv):       pytest -q
Or standalone (no pytest needed):             python tests/test_api_endpoints.py
"""
import asyncio
import os
import sys
from pathlib import Path

# ── Make `app` importable + set required env BEFORE importing settings ───────
# Resolve the backend dir from THIS file, so cwd doesn't matter.
BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
import bcrypt
import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401,E402  — register models on Base.metadata FIRST
from app.database import Base, get_session  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models import User  # noqa: E402


def _make_engine():
    """Fresh in-memory engine; StaticPool keeps the single connection alive."""
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


class _Counter:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []

    def check(self, label, cond):
        if cond:
            self.passed += 1
            print(f"  [OK ] {label}")
        else:
            self.failed += 1
            self.failures.append(label)
            print(f"  [FAIL] {label}")


async def _drive(transport, t):
    """Run the whole endpoint sequence, recording results into counter `t`."""
    check = t.check
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        # ── Health (no auth) ────────────────────────────────────────────────
        r = await c.get("/health")
        check("health 200", r.status_code == 200 and r.json()["status"] == "ok")

        # ── Auth required ───────────────────────────────────────────────────
        r = await c.get("/funds")
        check("funds without token → 401", r.status_code == 401)

        r = await c.post("/auth/login", json={"username": "admin", "password": "nope"})
        check("login wrong password → 401", r.status_code == 401)

        r = await c.post("/auth/login", json={"username": "admin", "password": "admin"})
        check("login ok → 200 + token", r.status_code == 200 and "access_token" in r.json())
        token = r.json()["access_token"]
        H = {"Authorization": f"Bearer {token}"}

        # ── Funds CRUD ──────────────────────────────────────────────────────
        r = await c.post("/funds", headers=H, json={
            "name": "Salary", "fund_type": "salary", "amount": 10000})
        check("create salary fund → 201", r.status_code == 201)
        salary_id = r.json()["id"]

        r = await c.post("/funds", headers=H, json={
            "name": "Savings Bucket", "fund_type": "other", "amount": 5000})
        check("create other fund → 201", r.status_code == 201)
        other_id = r.json()["id"]

        # duplicate name → 409
        r = await c.post("/funds", headers=H, json={
            "name": "Salary", "fund_type": "salary", "amount": 1})
        check("duplicate fund name → 409", r.status_code == 409)

        # bad fund_type → 422 (schema Literal)
        r = await c.post("/funds", headers=H, json={
            "name": "Bad", "fund_type": "wrong", "amount": 1})
        check("invalid fund_type → 422", r.status_code == 422)

        r = await c.get("/funds", headers=H)
        check("list funds → 2", r.status_code == 200 and len(r.json()) == 2)

        r = await c.get(f"/funds/{salary_id}", headers=H)
        check("get fund by id", r.status_code == 200 and r.json()["name"] == "Salary")

        r = await c.get("/funds/999999", headers=H)
        check("get missing fund → 404", r.status_code == 404)

        r = await c.put(f"/funds/{salary_id}", headers=H, json={
            "name": "Salary", "fund_type": "salary", "amount": 12000})
        check("update fund amount", r.status_code == 200 and r.json()["amount"] == 12000)

        # ── Categories ──────────────────────────────────────────────────────
        await c.post("/categories", headers=H, json={"name": "Food"})
        await c.post("/categories", headers=H, json={"name": "Rent"})
        # idempotent duplicate
        r = await c.post("/categories", headers=H, json={"name": "Food"})
        check("category idempotent add", r.status_code in (200, 201))
        r = await c.get("/categories", headers=H)
        check("list categories sorted", r.json() == ["Food", "Rent"])

        # ── Transactions ────────────────────────────────────────────────────
        # Salary fund: Rent 600 (2025-02), Food 300 (2025-01), Food 300 (2025-02)
        for cat, amt, date in [
            ("Rent", 600, "2025-02-01"),
            ("Food", 300, "2025-01-10"),
            ("Food", 300, "2025-02-15"),
        ]:
            r = await c.post("/transactions", headers=H, json={
                "fund_id": salary_id, "category": cat,
                "amount": amt, "txn_date": date})
            assert r.status_code == 201, r.text
        # Other fund: savings 2000
        await c.post("/transactions", headers=H, json={
            "fund_id": other_id, "category": "savings",
            "amount": 2000, "txn_date": "2025-02-20"})

        r = await c.get("/transactions", headers=H, params={"fund_id": salary_id})
        check("list txns for fund → 3 + fund_name join",
              r.status_code == 200 and len(r.json()) == 3
              and r.json()[0]["fund_name"] == "Salary")

        # ── NULL-date ordering parity (regression) ──────────────────────────
        # Desktop SQLite sorts NULL txn_date FIRST under ascending order; the
        # Postgres API must match (NULLS FIRST), not push undated rows to the end.
        r = await c.post("/transactions", headers=H, json={
            "fund_id": salary_id, "category": "Misc", "amount": 50})  # no txn_date
        assert r.status_code == 201, r.text
        r = await c.get("/transactions", headers=H, params={"fund_id": salary_id})
        listing = r.json()
        check("undated txn sorts FIRST (NULLS FIRST parity)",
              listing[0]["txn_date"] is None and listing[0]["category"] == "Misc")
        # Clean up so later totals (1200) stay intact.
        await c.delete(f"/transactions/{listing[0]['id']}", headers=H)

        # txn for missing fund → 404
        r = await c.post("/transactions", headers=H, json={
            "fund_id": 999999, "category": "X", "amount": 1})
        check("txn for missing fund → 404", r.status_code == 404)

        # ── Fund summary (parity formula) ───────────────────────────────────
        # Salary income 12000, expenses 1200 → remaining 10800
        r = await c.get(f"/funds/{salary_id}/summary", headers=H)
        s = r.json()
        check("fund summary expenses=1200", s["expenses"] == 1200)
        check("fund summary remaining=10800", s["remaining"] == 10800)

        r = await c.get("/funds/summaries", headers=H)
        summ = r.json()
        check("summaries keyed by id", str(salary_id) in summ or salary_id in summ)

        # ── BPI balance ─────────────────────────────────────────────────────
        r = await c.get("/bpi-balance", headers=H)
        check("bpi default 0", r.status_code == 200 and r.json()["balance"] == 0.0)
        r = await c.put("/bpi-balance", headers=H, json={"balance": 9000})
        check("bpi put → 9000", r.status_code == 200 and r.json()["balance"] == 9000)
        r = await c.get("/bpi-balance", headers=H)
        check("bpi get latest → 9000", r.json()["balance"] == 9000)

        # ── Dashboard totals ────────────────────────────────────────────────
        # non-other income=12000, non-other expenses=1200 → non_other_remaining=10800
        # other income=5000, other txn=2000 → total_savings=3000
        # bpi=9000 → missing_expenses = 9000 - 10800 = -1800
        r = await c.get("/dashboard/totals", headers=H)
        d = r.json()
        check("dash total_income=12000", d["total_income"] == 12000)
        check("dash total_expenses=1200", d["total_expenses"] == 1200)
        check("dash total_savings=3000", d["total_savings"] == 3000)
        check("dash non_other_remaining=10800", d["non_other_remaining"] == 10800)
        check("dash bpi_balance=9000", d["bpi_balance"] == 9000)
        check("dash missing_expenses=-1800", d["missing_expenses"] == -1800)
        check("dash fund_count=2", d["fund_count"] == 2)

        # ── Dashboard charts ────────────────────────────────────────────────
        r = await c.get("/dashboard/spending-over-time", headers=H)
        pts = r.json()
        # 2025-01: 300, 2025-02: 600+300+2000=2900
        check("spending-over-time months",
              pts == [{"month": "2025-01", "total": 300},
                      {"month": "2025-02", "total": 2900}])

        r = await c.get("/dashboard/expense-by-category", headers=H,
                        params={"fund_id": salary_id})
        cats = r.json()
        # Rent 600, Food 600 → sorted desc by total (ties keep both)
        check("expense-by-category total",
              sum(x["total"] for x in cats) == 1200 and len(cats) == 2)

        r = await c.get("/dashboard/years", headers=H)
        check("years = ['2025']", r.json() == ["2025"])

        # ── Reports ─────────────────────────────────────────────────────────
        r = await c.get("/reports/overview", headers=H, params={"fund_id": salary_id})
        o = r.json()
        check("overview total_spent=1200", o["total_spent"] == 1200)
        check("overview txn_count=3", o["txn_count"] == 3)
        check("overview biggest=Rent 600",
              o["biggest"]["category"] == "Rent" and o["biggest"]["amount"] == 600)
        # busiest month 2025-02 = 900 (Rent 600 + Food 300)
        check("overview busiest_month 2025-02/900",
              o["busiest_month"][0] == "2025-02" and o["busiest_month"][1] == 900)
        # most_frequent: Food appears 2× → ["Food", 2]
        check("overview most_frequent Food×2",
              o["most_frequent"][0] == "Food" and o["most_frequent"][1] == 2)

        r = await c.get("/reports/category-stats", headers=H, params={"fund_id": salary_id})
        cs = r.json()
        check("category-stats 2 rows sorted by total", len(cs) == 2 and cs[0]["total"] == 600)

        r = await c.get("/reports/fund-flows", headers=H)
        ff = r.json()
        # both funds present; salary out_flow=1200, other out_flow=2000
        check("fund-flows lists all funds", len(ff) == 2)
        salary_flow = next(f for f in ff if f["id"] == salary_id)
        check("fund-flows salary out=1200/net=-1200",
              salary_flow["out_flow"] == 1200 and salary_flow["net"] == -1200)

        # ── Delete cascade ──────────────────────────────────────────────────
        r = await c.delete(f"/funds/{salary_id}", headers=H)
        check("delete fund → 204", r.status_code == 204)
        r = await c.get("/transactions", headers=H, params={"fund_id": salary_id})
        check("txns gone after fund delete (cascade)", r.json() == [])


async def _run() -> _Counter:
    """Set up a fresh in-memory DB, wire the override, drive the endpoints."""
    engine = _make_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_session():
        async with session_factory() as s:
            yield s

    fastapi_app.dependency_overrides[get_session] = _override_get_session
    t = _Counter()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Seed the admin user (bcrypt hash matches "admin")
        async with session_factory() as s:
            s.add(User(
                username="admin",
                password_hash=bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode(),
            ))
            await s.commit()
        transport = httpx.ASGITransport(app=fastapi_app)
        await _drive(transport, t)
    finally:
        fastapi_app.dependency_overrides.pop(get_session, None)
        await engine.dispose()
    return t


def test_api_endpoints():
    """pytest entrypoint — fails if any endpoint check fails."""
    t = asyncio.run(_run())
    assert t.failed == 0, f"API checks failed: {t.failures}"


if __name__ == "__main__":
    counter = asyncio.run(_run())
    print(f"\n{'='*52}")
    print(f"PHASE 2 API E2E: {counter.passed} passed, {counter.failed} failed")
    print(f"{'='*52}")
    sys.exit(0 if counter.failed == 0 else 1)
