#!/usr/bin/env python3
"""Capture real local evidence. Never writes credentials or creates AWS resources."""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/evidence'
EVIDENCE.mkdir(parents=True, exist_ok=True)

def run(command, output, timeout=180):
    print('Running:', ' '.join(command), flush=True)
    process = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=timeout)
    (EVIDENCE / output).write_text('UTC: ' + datetime.now(timezone.utc).isoformat() +
        '\nCOMMAND: ' + ' '.join(command) + '\nEXIT: ' + str(process.returncode) + '\n\n' + process.stdout)
    print(process.stdout[-2000:], flush=True)
    if process.returncode:
        raise RuntimeError('Command failed; see ' + output)
    return process.stdout

def compose(*args):
    return ['docker', 'compose', *args]

def request(path, data=None, expected=200):
    req = urllib.request.Request('http://127.0.0.1:8080' + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    assert response.status == expected, (path, response.status, expected)
    return json.load(response)

def wait_ready():
    for _ in range(45):
        try:
            request('/health/ready')
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError('Readiness did not recover')

def application():
    run(compose('ps'), 'docker-status.log')
    run([sys.executable, 'scripts/smoke.py'], 'app-smoke.log')
    request('/api/notes', {'message': ''}, expected=400)
    marker = 'recovery-' + datetime.now(timezone.utc).isoformat()
    created = request('/api/notes', {'message': marker}, expected=201)
    run(compose('exec', '-T', 'backend', 'python', '-c',
        'import os, signal; os.kill(1, signal.SIGKILL)'), 'backend-crash.log')
    wait_ready()
    assert any(n['id'] == created['id'] for n in request('/api/notes'))
    run(compose('up', '-d', '--force-recreate', 'backend'), 'backend-recreate.log')
    wait_ready()
    assert any(n['id'] == created['id'] for n in request('/api/notes'))
    run(compose('stop', 'db'), 'database-stop.log')
    try:
        request('/health/live')
        request('/api/notes', expected=503)
    finally:
        run(compose('start', 'db'), 'database-start.log')
    wait_ready()
    run(compose('up', '-d', '--force-recreate', 'db'), 'database-recreate.log')
    wait_ready()
    assert any(n['id'] == created['id'] for n in request('/api/notes'))
    run(['docker', 'inspect', 'thmanyah-assessment-backend-1', '--format',
         'restart={{.HostConfig.RestartPolicy.Name}} memory={{.HostConfig.Memory}} cpu={{.HostConfig.NanoCpus}} user={{.Config.User}} readonly={{.HostConfig.ReadonlyRootfs}}'], 'resource-limits.log')
    result = dict(test='recovery', process_crash='PASS', backend_recreate='PASS',
                  db_failure_503='PASS', named_volume_persistence='PASS',
                  marker_id=created['id'], timestamp=datetime.now(timezone.utc).isoformat())
    (EVIDENCE / 'app-recovery.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)

def s3():
    run(['docker', 'compose', '-f', 'compose.s3.yaml', 'run', '--rm',
         '-v', str(ROOT) + ':/repo:ro', 's3-worker', 'python', '/repo/tests/test_s3.py'], 's3-tests.log')
    run(['docker', 'compose', '-f', 'compose.s3.yaml', 'exec', '-T', 'nodered',
         'node', '-e', "fetch('http://s3-worker:9000/copy',{method:'POST'}).then(async r=>{console.log(r.status,await r.text());if(!r.ok)process.exit(1)}).catch(e=>{console.error(e);process.exit(1)})"], 'nodered-worker.log')

def storage():
    command = ['docker', 'compose', '-f', 'compose.storage.yaml', 'exec', '-T', 'client']
    run(command + ['findmnt', '/mnt/media'], 'smb-mount.log')
    run(command + ['sh', '-c', 'printf "assessment round trip\\n" > /mnt/media/round-trip.txt; sync; cat /mnt/media/round-trip.txt; cat /proc/fs/cifs/DebugData'], 'smb-roundtrip.log')
    run(command + ['fio', '--name=share-sequential', '--filename=/mnt/media/fio-test.bin',
        '--size=32m', '--rw=write', '--bs=1m', '--ioengine=sync', '--direct=1',
        '--fsync_on_close=1', '--output-format=json', '--unlink=1'], 'smb-fio.log')
    run(command + ['python', '-c', "import urllib.request;print(urllib.request.urlopen('http://localhost:9101/metrics').read().decode())"], 'storage-probe.log')
    run(['docker', 'compose', '-f', 'compose.storage.yaml', 'exec', '-T', 'prometheus',
         'promtool', 'check', 'rules', '/etc/prometheus/alerts.yml'], 'storage-alert-rules.log')
    run(['docker', 'compose', '-f', 'compose.storage.yaml', 'run', '--rm', 'xfs'], 'xfs-sparse.log', 240)

def terraform():
    base = ['docker', 'run', '--rm', '-v', str(ROOT / 'infra') + ':/work', '-w', '/work',
            'hashicorp/terraform:1.14.7']
    run(base + ['fmt', '-check', '-recursive'], 'terraform-format.log')
    run(base + ['validate', '-no-color'], 'terraform-validate.log')

def streaming():
    base = ['docker', 'run', '--rm', '--cpus=2', '--memory=1g', '-v',
            str(EVIDENCE) + ':/evidence', 'thmanyah-streaming']
    run(base, 'hevc-encode.log')
    result = run(base + ['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                         '-of', 'json', '/evidence/local-hevc.ts'], 'hevc-probe.log')
    probe = json.loads(result)
    video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
    assert video['codec_name'] == 'hevc' and video['width'] == 1920 and video['height'] == 1080
    assert video['r_frame_rate'] == '25/1' and audio['codec_name'] == 'aac'
    packet_result = run(base + ['ffprobe', '-v', 'error', '-show_packets',
        '-show_entries', 'packet=stream_index,size,pts_time,duration_time', '-of', 'json',
        '/evidence/local-hevc.ts'], 'hevc-packets.log')
    packets = json.loads(packet_result)['packets']
    rates = {}
    for stream in probe['streams']:
        selected = [p for p in packets if p['stream_index'] == stream['index'] and 'pts_time' in p]
        start = min(float(p['pts_time']) for p in selected)
        end = max(float(p['pts_time']) + float(p.get('duration_time', '0')) for p in selected)
        rates[stream['codec_type']] = round(sum(int(p['size']) for p in selected) * 8 / (end - start))
    summary = {'video_codec': video['codec_name'], 'resolution': '1920x1080', 'fps': 25,
               'audio_codec': audio['codec_name'], 'configured_video_bps': 12000000,
               'configured_audio_bps': 192000, 'measured_elementary_bps': rates,
               'container_bps': int(probe['format']['bit_rate']), 'aws_transmission': 'not executed'}
    (EVIDENCE / 'streaming-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)
    run(base + ['python', 'render-config.py', '--bucket', 'assessment-example-archive',
        '--role-arn', 'arn:aws:iam::123456789012:role/assessment-medialive', '--secret-arn',
        'arn:aws:secretsmanager:eu-west-1:123456789012:secret:assessment-srt-example'], 'medialive-schema.log')

def alerts():
    base = ['docker', 'compose', '-f', 'compose.storage.yaml', 'exec', '-T', 'client']
    run(base + ['umount', '/mnt/media'], 'alert-unmount.log')
    try:
        for _ in range(30):
            response = json.load(urllib.request.urlopen('http://127.0.0.1:9090/api/v1/alerts', timeout=5))
            if any(a['labels'].get('alertname') == 'ShareUnavailable' and a['state'] == 'firing'
                   for a in response['data']['alerts']):
                (EVIDENCE / 'alert-firing.json').write_text(json.dumps(response, indent=2) + '\n')
                print('ShareUnavailable reached firing state PASS', flush=True)
                break
            time.sleep(3)
        else:
            raise RuntimeError('Expected ShareUnavailable alert did not fire')
    finally:
        run(base + ['mount', '-t', 'cifs', '//samba/media', '/mnt/media', '-o',
            'credentials=/tmp/smb-credentials,vers=3.1.1,seal,nosuid,nodev,noexec'], 'alert-remount.log')
    for _ in range(15):
        response = json.load(urllib.request.urlopen('http://127.0.0.1:9090/api/v1/alerts', timeout=5))
        if not any(a['labels'].get('alertname') == 'ShareUnavailable' for a in response['data']['alerts']):
            (EVIDENCE / 'alert-resolved.json').write_text(json.dumps(response, indent=2) + '\n')
            print('ShareUnavailable resolved after remount PASS', flush=True)
            return
        time.sleep(3)
    raise RuntimeError('Alert did not resolve after remount')

for suite in sys.argv[1:] or ['app', 's3', 'storage', 'terraform']:
    {'app': application, 's3': s3, 'storage': storage, 'terraform': terraform,
     'streaming': streaming, 'alerts': alerts}[suite]()
