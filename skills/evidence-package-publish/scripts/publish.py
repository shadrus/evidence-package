#!/usr/bin/env python3
"""Configure credentials locally and publish an evidence-package JSON file."""

import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


def config_path():
    root = os.environ.get("EVIDENCE_CONFIG_HOME")
    if root:
        return Path(root) / "client.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "evidence-package" / "client.json"


def service_origin(value):
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("service URL must be an HTTP(S) origin")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("HTTPS is required for a remote service")
    return value.rstrip("/")


def save_config(origin, key):
    path = config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(prefix=".client-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"base_url": origin, "api_key": key}, stream)
            stream.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_config():
    path = config_path()
    if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError("config file is readable by others; run chmod 600 on it")
    with path.open(encoding="utf-8") as stream:
        config = json.load(stream)
    config["base_url"] = service_origin(config["base_url"])
    return config


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def publish(package_path, no_preview=False, opener=None):
    config = load_config()
    raw = Path(package_path).read_bytes()
    if not isinstance(json.loads(raw), dict):
        raise ValueError("package must be a JSON object")
    endpoint = config["base_url"] + "/v1/packages"
    if no_preview:
        endpoint += "?preview=none"
    headers = {"Content-Type": "application/json"}
    if config.get("api_key"):
        headers["Authorization"] = "Bearer " + config["api_key"]
    request = urllib.request.Request(endpoint, data=raw, headers=headers, method="POST")
    transport = opener or urllib.request.build_opener(NoRedirect)
    with transport.open(request, timeout=30) as response:
        result = json.load(response)
    if result.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("server returned a different package hash")
    share_url = result.get("url")
    if not isinstance(share_url, str):
        raise ValueError("server returned an unexpected share URL")
    parsed = urllib.parse.urlsplit(share_url)
    if not re.fullmatch(r"/p/[0-9a-f]{32}", parsed.path) or parsed.query or parsed.fragment:
        raise ValueError("server returned an unexpected share URL")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")):
        raise ValueError("server returned an insecure share URL")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    configure = commands.add_parser("configure", help="save service URL and optional API key")
    configure.add_argument("--base-url", required=True)
    publication = commands.add_parser("publish", help="publish a package JSON file")
    publication.add_argument("package")
    publication.add_argument("--no-preview", action="store_true")
    commands.add_parser("clear-key", help="remove the locally stored API key")
    args = parser.parse_args(argv)
    try:
        if args.command == "configure":
            origin = service_origin(args.base_url)
            key = getpass.getpass("API key (leave blank for anonymous publication): ").strip()
            save_config(origin, key)
            print("Configured " + origin + (" with an API key" if key else " for anonymous publication"))
        elif args.command == "clear-key":
            config = load_config()
            save_config(config["base_url"], "")
            print("Local API key removed")
        else:
            result = publish(args.package, args.no_preview)
            print(result["url"])
            if result.get("expires_at"):
                print("Expires: " + result["expires_at"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError, urllib.error.URLError) as error:
        print("evidence publish: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
