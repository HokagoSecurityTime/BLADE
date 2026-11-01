import asyncio
import sqlite3
from pathlib import Path

from common.redis_detections import stream_name, decode_records
from common.schema import OwnerLookup
from proxy.cache import LookupCache
from proxy.lookup import BatchedLookup, LookupError
from tests.test_alerts import record


def test_transport_batch_preserves_records_and_legacy_entries(monkeypatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    first = record()
    second = first.model_copy(update={'request_id': 'second', 'mode': 'enforce', 'would_block': False})
    payload = '[' + first.model_dump_json() + ',' + second.model_dump_json() + ']'
    assert decode_records({'records': payload}) == [first, second]
    assert decode_records({'record': first.model_dump_json()}) == [first]


def test_explicit_stream_namespace_survives_different_mount_paths(monkeypatch) -> None:
    monkeypatch.setenv('BLADE_DETECTION_STREAM_NAMESPACE', 'isolated-test')
    monkeypatch.setenv('BLADE_DB_DSN', 'sqlite:///admin/demo.db')
    admin_stream = stream_name()
    monkeypatch.setenv('BLADE_DB_DSN', 'sqlite:///file:/proxy/demo.db?mode=ro')
    assert stream_name() == admin_stream


def test_inventory_overflow_disables_negative_shortcut(monkeypatch) -> None:
    monkeypatch.delenv('BLADE_REDIS_URL', raising=False)
    cache = LookupCache()
    cache._inventory_complete = True
    cache._known_remote_keys = {str(i) for i in range(100000)}
    cache._remember_remote_key('overflow')
    assert not cache._inventory_complete
    assert not cache._known_remote_keys


def test_bad_query_does_not_fail_other_requests_in_batch(tmp_path: Path) -> None:
    database = tmp_path / 'owners.db'
    connection = sqlite3.connect(database)
    connection.execute('CREATE TABLE orders (id TEXT, user_id TEXT)')
    connection.execute("INSERT INTO orders VALUES ('1', 'user_1')")
    connection.commit()
    connection.close()

    async def run() -> None:
        lookup = BatchedLookup('sqlite:///' + str(database))
        good = OwnerLookup(table='orders', id_col='id', owner_col='user_id')
        bad = good.model_copy(update={'table': 'missing_table'})
        results = await asyncio.gather(lookup.get(bad, '1'), lookup.get(good, '1'), return_exceptions=True)
        assert isinstance(results[0], LookupError)
        assert results[1] == {'user_id': 'user_1'}
        await lookup.close()

    asyncio.run(run())
