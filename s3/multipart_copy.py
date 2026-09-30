"""Bounded parallel, server-side S3 multipart copy; never downloads object data."""
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import quote

import boto3
from botocore.config import Config

MIB = 1024 ** 2
GIB = 1024 ** 3
# S3's current maximum is 10,000 parts of up to 5 GiB (48.8 TiB).
MAX_PART = 5 * GIB
MAX_PARTS = 10_000
MAX_OBJECT = MAX_PART * MAX_PARTS


def plan(size, preferred=64 * MIB):
    if not isinstance(size, int) or size < 0 or size > MAX_OBJECT:
        raise ValueError("object size outside S3 multipart limits")
    if not 5 * MIB <= preferred <= MAX_PART:
        raise ValueError("preferred part size must be 5 MiB to 5 GiB")
    part_size = max(preferred, math.ceil(max(size, 1) / MAX_PARTS))
    count = math.ceil(size / part_size)
    return part_size, count


def log(event, **fields):
    print(json.dumps(dict(timestamp=datetime.now(timezone.utc).isoformat(),
                          event=event, **fields)), flush=True)


def client():
    # Local emulator variables are provided only in compose.s3.yaml.
    # On AWS use the SDK credential chain, preferably an IAM role.
    endpoint = os.getenv("S3_ENDPOINT")
    return boto3.client("s3", endpoint_url=endpoint,
        config=Config(region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                      retries={"max_attempts": 5, "mode": "standard"},
                      max_pool_connections=32, s3={"addressing_style": "path"}))


def copy_object(s3, source_bucket, key, destination_bucket, destination_key=None,
                preferred=64 * MIB, concurrency=8):
    destination_key = destination_key or key
    if source_bucket == destination_bucket and key == destination_key:
        raise ValueError("source and destination must differ")
    if not 1 <= concurrency <= 32:
        raise ValueError("concurrency must be 1 to 32")
    head = s3.head_object(Bucket=source_bucket, Key=key)
    size = head["ContentLength"]
    part_size, part_count = plan(size, preferred)
    source = quote(source_bucket + "/" + key, safe="/")
    # Pin a version if available; otherwise reject a source changing between parts.
    version = head.get("VersionId")
    if version and version != "null":
        source += "?versionId=" + quote(version, safe="")
    started = time.monotonic()
    common = dict(Bucket=destination_bucket, Key=destination_key,
                  Metadata=head.get("Metadata", {}),
                  ContentType=head.get("ContentType", "application/octet-stream"))
    log("copy_started", bytes=size, parts=part_count, part_size=part_size,
        concurrency=concurrency, source_version=version)
    if size == 0:
        s3.copy_object(**common, CopySource=source, CopySourceIfMatch=head["ETag"],
                       MetadataDirective="REPLACE")
        return dict(bytes=0, parts=0, seconds=round(time.monotonic() - started, 3))
    upload_id = s3.create_multipart_upload(**common)["UploadId"]

    def copy_part(number):
        start = (number - 1) * part_size
        end = min(size - 1, start + part_size - 1)
        result = s3.upload_part_copy(Bucket=destination_bucket, Key=destination_key,
            UploadId=upload_id, PartNumber=number, CopySource=source,
            CopySourceIfMatch=head["ETag"], CopySourceRange=f"bytes={start}-{end}")
        log("part_completed", part=number, bytes=end - start + 1)
        return dict(PartNumber=number, ETag=result["CopyPartResult"]["ETag"])

    try:
        # All futures finish before abort; no workers can upload after cleanup.
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(copy_part, n) for n in range(1, part_count + 1)]
            parts = [future.result() for future in as_completed(futures)]
        s3.complete_multipart_upload(Bucket=destination_bucket, Key=destination_key,
            UploadId=upload_id, MultipartUpload={"Parts": sorted(parts, key=lambda p: p["PartNumber"])})
    except BaseException:
        try:
            s3.abort_multipart_upload(Bucket=destination_bucket, Key=destination_key, UploadId=upload_id)
            log("upload_aborted")
        except Exception as abort_error:
            log("abort_failed", error_type=type(abort_error).__name__)
        raise
    target = s3.head_object(Bucket=destination_bucket, Key=destination_key)
    if target["ContentLength"] != size:
        raise RuntimeError("destination size verification failed")
    seconds = time.monotonic() - started
    result = dict(bytes=size, parts=part_count, seconds=round(seconds, 3),
                  mib_per_second=round(size / MIB / max(seconds, 0.001), 2))
    log("copy_completed", **result)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_bucket")
    parser.add_argument("key")
    parser.add_argument("destination_bucket")
    parser.add_argument("--destination-key")
    parser.add_argument("--part-mib", type=int, default=64)
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()
    copy_object(client(), args.source_bucket, args.key, args.destination_bucket,
                args.destination_key, args.part_mib * MIB, args.concurrency)
