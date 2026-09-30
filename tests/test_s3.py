import importlib.util
import hashlib
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("multipart_copy", Path(__file__).parents[1] / "s3/multipart_copy.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MultipartTests(unittest.TestCase):
    def test_planner_boundaries(self):
        self.assertEqual(module.plan(0), (64 * module.MIB, 0))
        for size in [1, 5 * module.MIB, 1 * 1024**4, 5 * 1024**4, module.MAX_OBJECT]:
            part_size, count = module.plan(size)
            self.assertLessEqual(count, 10000)
            self.assertLessEqual(part_size, 5 * module.GIB)
            self.assertGreaterEqual(part_size, 5 * module.MIB)
            self.assertGreaterEqual(part_size * count, size)
        with self.assertRaises(ValueError):
            module.plan(module.MAX_OBJECT + 1)

    def test_copy_roundtrip(self):
        s3 = module.client()
        for bucket in ["broadcast-source", "broadcast-archive"]:
            try:
                s3.create_bucket(Bucket=bucket)
            except s3.exceptions.BucketAlreadyOwnedByYou:
                pass
        data = b"broadcast-assessment" * (700000)
        s3.put_object(Bucket="broadcast-source", Key="demo.bin", Body=data,
                      Metadata={"purpose": "assessment"})
        result = module.copy_object(s3, "broadcast-source", "demo.bin", "broadcast-archive",
                                    preferred=5 * module.MIB, concurrency=3)
        copied = s3.get_object(Bucket="broadcast-archive", Key="demo.bin")["Body"].read()
        self.assertGreaterEqual(result["parts"], 3)
        self.assertEqual(hashlib.sha256(data).digest(), hashlib.sha256(copied).digest())
        self.assertEqual(s3.head_object(Bucket="broadcast-archive", Key="demo.bin")["Metadata"],
                         {"purpose": "assessment"})
        print("SHA256 byte-for-byte verification PASS")

    def test_abort_on_failure(self):
        class FailureClient:
            aborted = False
            def head_object(self, **kwargs): return {"ContentLength": 6 * module.MIB, "ETag": '"v1"'}
            def create_multipart_upload(self, **kwargs): return {"UploadId": "test"}
            def upload_part_copy(self, **kwargs): raise RuntimeError("injected part failure")
            def abort_multipart_upload(self, **kwargs): self.aborted = True
        s3 = FailureClient()
        with self.assertRaises(RuntimeError):
            module.copy_object(s3, "a", "test", "b", preferred=5 * module.MIB)
        self.assertTrue(s3.aborted)


if __name__ == "__main__":
    unittest.main()
