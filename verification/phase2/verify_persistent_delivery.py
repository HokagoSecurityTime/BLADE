"""Restart only the new, unused detection Redis before application deployment."""
import json
from pathlib import Path
import subprocess
import time
import uuid

DOCKER = r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
NAME = 'blade-phase2-detection-redis-1'


def command(*arguments: str) -> str:
    return subprocess.run([DOCKER, *arguments], check=True, capture_output=True,
                          text=True, timeout=30).stdout.strip()


def main() -> None:
    info = json.loads(command('inspect', NAME))[0]
    labels = info['Config']['Labels']
    assert labels['com.docker.compose.project'] == 'blade-phase2'
    assert labels['com.docker.compose.service'] == 'detection-redis'
    identifier = info['Id']
    assert 'appendonly' in ' '.join(info['Config']['Cmd'])
    key = 'blade:verification:persistence:' + uuid.uuid4().hex
    def redis(*arguments: str) -> str:
        return command('exec', identifier, 'redis-cli', '--raw', *arguments)
    entry = redis('XADD', key, '*', 'record', 'isolated-persistence-fixture')
    # everysec is not synchronous durability; wait for its configured fsync.
    time.sleep(2)
    before = redis('XRANGE', key, '-', '+')
    try:
        command('kill', identifier)
    finally:
        command('start', identifier)
    for _ in range(100):
        try:
            if redis('PING') == 'PONG':
                break
        except subprocess.CalledProcessError:
            pass
        time.sleep(.1)
    assert redis('XRANGE', key, '-', '+') == before
    assert entry in before
    assert redis('DEL', key) == '1'
    result = dict(passed=True, container=NAME, container_id=identifier,
                  appendonly=True, fsync='everysec', persisted_after_kill=True,
                  final_ping=redis('PING'), limitation='Unflushed recent writes are not guaranteed')
    Path('verification/phase2/persistent-delivery-result.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
