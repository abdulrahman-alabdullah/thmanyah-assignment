"""A write+fsync+read probe checks the mounted share, beyond TCP reachability."""
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

metrics = "share_probe_success 0\n"
command = """import os; p='/mnt/media/.service-probe';
with open(p,'wb') as f: f.write(b'probe'); f.flush(); os.fsync(f.fileno())
assert open(p,'rb').read()==b'probe'
os.unlink(p)
"""

def probe():
    global metrics
    while True:
        start = time.monotonic()
        ok = 0
        try:
            if not os.path.ismount('/mnt/media'):
                raise RuntimeError('not mounted')
            subprocess.run(['python', '-c', command], check=True, timeout=5, capture_output=True)
            usage = os.statvfs('/mnt/media')
            available = usage.f_bavail * usage.f_frsize
            total = usage.f_blocks * usage.f_frsize
            ok = 1
        except Exception:
            available = total = 0
        metrics = (f'share_probe_success {ok}\nshare_probe_duration_seconds {time.monotonic()-start}\n'
                   f'share_available_bytes {available}\nshare_total_bytes {total}\n')
        time.sleep(10)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/metrics':
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4')
        self.end_headers()
        self.wfile.write(metrics.encode())

threading.Thread(target=probe, daemon=True).start()
HTTPServer(('0.0.0.0', 9101), Handler).serve_forever()
