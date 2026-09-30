#!/usr/bin/env python3
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'docs/evidence'
def capture(command, filename):
    r = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (E / filename).write_text('UTC: ' + datetime.now(timezone.utc).isoformat() +
        '\nCOMMAND: ' + ' '.join(command) + '\nEXIT: ' + str(r.returncode) + '\n' + r.stdout)
    assert r.returncode == 0, r.stdout
    print(r.stdout[-1500:], flush=True)
    return r.stdout

capture(['ansible-playbook', '-i', 'infra/ansible/inventory.example.yml',
         'infra/ansible/site.yml', '--syntax-check'], 'ansible-syntax.log')
capture(['bash', 'scripts/backup.sh'], 'postgres-backup.log')
backup = sorted((ROOT / 'backups').glob('*.dump'))[-1]
prefix = ['docker', 'compose', 'exec', '-T', 'db']
capture(prefix + ['createdb', '-U', 'broadcast', 'broadcast_restore'], 'postgres-restore-create.log')
with backup.open('rb') as stream:
    result = subprocess.run(prefix + ['pg_restore', '-U', 'broadcast', '-d', 'broadcast_restore', '--exit-on-error'],
                            cwd=ROOT, stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode == 0, result.stdout
original = capture(prefix + ['psql', '-U', 'broadcast', '-d', 'broadcast', '-Atc',
                            'SELECT count(*) FROM notes'], 'postgres-original-count.log').strip()
restored = capture(prefix + ['psql', '-U', 'broadcast', '-d', 'broadcast_restore', '-Atc',
                            'SELECT count(*) FROM notes'], 'postgres-restored-count.log').strip()
assert original == restored and int(restored) > 0
capture(prefix + ['dropdb', '-U', 'broadcast', 'broadcast_restore'], 'postgres-restore-cleanup.log')
(E / 'postgres-restore.json').write_text(json.dumps({'original_count': int(original),
    'restored_count': int(restored), 'result': 'PASS'}, indent=2) + '\n')

command = ['docker', 'run', '--name', 'thmanyah-oom-proof', '--memory=64m', '--memory-swap=64m',
           '--cpus=0.25', 'thmanyah-assessment-backend', 'python', '-c',
           'chunks=[bytearray(8*1024*1024) for _ in range(100)]']
result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
assert result.returncode == 137, result.stdout
oom = capture(['docker', 'inspect', 'thmanyah-oom-proof', '--format',
               'oom={{.State.OOMKilled}} exit={{.State.ExitCode}} limit={{.HostConfig.Memory}}'], 'oom-limit.log')
assert 'oom=true' in oom
capture(['docker', 'rm', 'thmanyah-oom-proof'], 'oom-cleanup.log')

since = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
req = urllib.request.Request('http://127.0.0.1:1880/inject/copy-trigger', data=b'', method='POST')
with urllib.request.urlopen(req, timeout=10) as response:
    assert response.status == 200
time.sleep(3)
logs = capture(['docker', 'compose', '-f', 'compose.s3.yaml', 'logs', '--since', since, 's3-worker', 'nodered'],
               'nodered-flow.log')
assert 'copy_completed' in logs and 'statusCode: 200' in logs
print('PASS: syntax, database restore, isolated OOM limit, Node-RED flow trigger', flush=True)
