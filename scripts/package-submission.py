#!/usr/bin/env python3
"""Create a source archive and verify that local credential values are absent."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
archive = root / 'Thmanyah-Assessment-Submission.zip'
excluded_dirs = {'.git', '.terraform', '__pycache__', 'secrets', 'backups', 'tmp'}
excluded_suffixes = {'.pyc', '.ts', '.img', '.tfvars', '.pem', '.key', '.tfplan'}
credentials = [p.read_bytes().strip() for p in (root / 'secrets').glob('*.txt')]
files = []
for path in sorted(root.rglob('*')):
    if not path.is_file() or path == archive:
        continue
    relative = path.relative_to(root)
    if any(part in excluded_dirs for part in relative.parts):
        continue
    if path.suffix in excluded_suffixes or '.tfstate' in path.name or path.name == '.DS_Store':
        continue
    content = path.read_bytes()
    if any(value and value in content for value in credentials):
        raise RuntimeError('Credential value detected in ' + str(relative))
    files.append((path, relative))
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
    for path, relative in files:
        output.write(path, 'thmanyah-assessment/' + str(relative))
    output.writestr('thmanyah-assessment/secrets/.gitkeep', '')
with zipfile.ZipFile(archive) as output:
    assert output.testzip() is None
    names = output.namelist()
    assert not any(name.endswith('.txt') and '/secrets/' in name for name in names)
print(json.dumps({'archive': str(archive), 'files': len(names), 'bytes': archive.stat().st_size,
                  'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'credential_scan': 'PASS', 'zip_integrity': 'PASS'}, indent=2))
