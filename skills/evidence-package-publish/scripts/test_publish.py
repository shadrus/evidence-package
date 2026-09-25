import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit


SCRIPT = Path(__file__).with_name("publish.py")
spec = importlib.util.spec_from_file_location("evidence_publish", SCRIPT)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class Response:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self, *args):
        return self.body.read(*args)


class Opener:
    def __init__(self, digest, share_origin=None):
        self.request = None
        self.digest = digest
        self.share_origin = share_origin

    def open(self, request, timeout):
        self.request = request
        assert timeout == 30
        parsed = urlsplit(request.full_url)
        origin = self.share_origin or f"{parsed.scheme}://{parsed.netloc}"
        body = json.dumps({"url": origin + "/p/" + "a" * 32, "sha256": self.digest}).encode()
        return Response(io.BytesIO(body))


class PublishTest(unittest.TestCase):
    def test_configure_and_publish_original_bytes_with_key(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"EVIDENCE_CONFIG_HOME": directory}):
            publisher.save_config("https://api.evidence.example", "secret-key")
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(publisher.config_path().stat().st_mode), 0o600)
            package = Path(directory) / "package.json"
            raw = b'{ "task": "preserve spaces" }\n'
            package.write_bytes(raw)
            opener = Opener(hashlib.sha256(raw).hexdigest(), "https://evidence.example")
            result = publisher.publish(package, no_preview=True, opener=opener)
            self.assertEqual(result["url"], "https://evidence.example/p/" + "a" * 32)
            self.assertEqual(opener.request.full_url, "https://api.evidence.example/v1/packages?preview=none")
            self.assertEqual(opener.request.data, raw)
            self.assertEqual(opener.request.get_header("Authorization"), "Bearer secret-key")

    def test_anonymous_publish_sends_no_auth_header(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"EVIDENCE_CONFIG_HOME": directory}):
            publisher.save_config("http://127.0.0.1:8080", "")
            package = Path(directory) / "package.json"
            package.write_text("{}")
            opener = Opener(hashlib.sha256(b"{}").hexdigest())
            publisher.publish(package, opener=opener)
            self.assertIsNone(opener.request.get_header("Authorization"))
            self.assertEqual(opener.request.full_url, "http://127.0.0.1:8080/v1/packages")


if __name__ == "__main__":
    unittest.main()
