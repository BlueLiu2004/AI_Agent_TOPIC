"""Run existing fake-service tests with dotenv and outbound connections disabled."""
import os
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

video = Path(__file__).resolve().parents[1]
repo = video.parent
# Keep OS essentials only; do not inherit provider credentials or app overrides.
allowed = {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}
for name in list(os.environ):
    if name.upper() not in allowed:
        del os.environ[name]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
sys.dont_write_bytecode = True
sys.path.insert(0, str(repo))
os.chdir(repo)
import dotenv
original_connect = socket.socket.connect

def offline(*args, **kwargs):
    raise RuntimeError("Outbound network disabled for tutorial validation")

def local_connect(sock, address):
    # Windows asyncio creates its wake-up socketpair through loopback TCP.
    if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
        return original_connect(sock, address)
    return offline()

with patch.object(dotenv, "load_dotenv", return_value=False), patch.object(
    socket.socket, "connect", new=local_connect
), patch.object(socket, "create_connection", side_effect=offline):
    suite = unittest.defaultTestLoader.discover(str(repo / "tests"), pattern="test_workflow.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.testsRun == 14, result.testsRun
sys.exit(0 if result.wasSuccessful() else 1)
