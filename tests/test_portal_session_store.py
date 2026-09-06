from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from specvora.portal_session_store import PortalSessionStore


def test_mfa_counter_is_claimed_atomically_once(tmp_path):
    store = PortalSessionStore(tmp_path / "state.db")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.claim_mfa_counter("user", 42), range(4)))
    assert results.count(True) == 1
    assert results.count(False) == 3
    assert store.claim_mfa_counter("user", 41) is False
    assert store.claim_mfa_counter("user", 43) is True


def test_session_registration_expiry_and_revocation(tmp_path):
    store = PortalSessionStore(tmp_path / "state.db")
    now = datetime(2026, 9, 6, tzinfo=UTC)
    store.register_session("session-1", "user", now + timedelta(minutes=5))
    assert store.session_is_active("session-1", now)
    store.revoke_session("session-1")
    assert not store.session_is_active("session-1", now)
    assert not store.session_is_active("missing", now)
