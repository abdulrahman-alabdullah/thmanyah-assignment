import os
import threading
import importlib.util
from flask import Flask, jsonify

spec = importlib.util.spec_from_file_location("multipart_copy", "/work/multipart_copy.py")
copy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(copy)
app = Flask(__name__)
lock = threading.Lock()


@app.post("/copy")
def run():
    # The demo accepts no caller-supplied bucket names, credentials, or code.
    if not lock.acquire(blocking=False):
        return jsonify(error="copy already running"), 409
    try:
        return jsonify(copy.copy_object(copy.client(), os.getenv("SOURCE_BUCKET", "broadcast-source"),
            os.getenv("SOURCE_KEY", "demo.bin"), os.getenv("DESTINATION_BUCKET", "broadcast-archive"),
            preferred=int(os.getenv("PART_MIB", "5")) * copy.MIB))
    except Exception as error:
        copy.log("copy_failed", error_type=type(error).__name__)
        return jsonify(error="copy failed; inspect worker logs"), 502
    finally:
        lock.release()
