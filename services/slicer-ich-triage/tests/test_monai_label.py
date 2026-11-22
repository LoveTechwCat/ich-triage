"""Tests for ICHTriageLib.monai_label, run outside Slicer with plain pytest."""

import http.server
import json
import socket
import threading
import time
from pathlib import Path

import pytest

from ICHTriageLib import monai_label

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# --- URLs -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://localhost:8000", "http://localhost:8000"),
        ("http://localhost:8000/", "http://localhost:8000"),
        ("  https://monai.example.org:8443/api//  ", "https://monai.example.org:8443/api"),
        ("HTTP://127.0.0.1:8000", "http://127.0.0.1:8000"),
        ("http://[::1]:8000", "http://[::1]:8000"),
    ],
)
def test_normalize_server_url_accepts_http_urls(raw, expected):
    assert monai_label.normalize_server_url(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        None,
        "localhost:8000",
        "ftp://localhost:8000",
        "http://",
        "http://:8000",
        "http://localhost:99999",
        "http://localhost:8000/?x=1",
        "http://localhost:8000/#info",
        "http://user:secret@localhost:8000",
    ],
)
def test_normalize_server_url_rejects_bad_urls(raw):
    with pytest.raises(monai_label.UrlError):
        monai_label.normalize_server_url(raw)


def test_normalize_dicomweb_url_allows_empty():
    assert monai_label.normalize_dicomweb_url("") == ""
    assert monai_label.normalize_dicomweb_url(None) == ""
    assert monai_label.normalize_dicomweb_url("  ") == ""


def test_normalize_dicomweb_url_keeps_path():
    url = "http://pacs:8080/dcm4chee-arc/aets/DCM4CHEE/rs/"
    assert monai_label.normalize_dicomweb_url(url) == "http://pacs:8080/dcm4chee-arc/aets/DCM4CHEE/rs"


def test_normalize_dicomweb_url_rejects_non_http():
    with pytest.raises(monai_label.UrlError, match="PACS DICOMweb URL"):
        monai_label.normalize_dicomweb_url("dicom://pacs:11112")


# --- Parsing /info/ ---------------------------------------------------------


def test_parse_info_without_trainers():
    info = monai_label.parse_info(load_fixture("info_radiology_no_trainers.json"))
    assert info.name == "MONAILabel - Radiology (0.8.6)"
    assert info.version == "0.8.6"
    assert info.labels == ("spleen",)
    assert [model.name for model in info.models] == ["segmentation_spleen", "Histogram+GraphCut"]
    spleen = info.models[0]
    assert (spleen.type, spleen.dimension, spleen.labels) == ("segmentation", 3, ("spleen",))
    assert info.models[1].type == "scribbles"
    assert info.models[1].labels == ()
    assert info.trainers == ()
    assert info.strategies == ("random", "first")
    assert (info.datastore_total, info.datastore_completed) == (78, 0)


def test_parse_info_with_trainer():
    info = monai_label.parse_info(load_fixture("info_radiology_with_trainer.json"))
    assert [(t.name, t.description) for t in info.trainers] == [
        ("segmentation_spleen", "Train Spleen Segmentation Model")
    ]
    assert info.datastore_completed == 12


def test_parse_info_sorts_label_mapping_by_index():
    data = load_fixture("info_radiology_no_trainers.json")
    data["models"]["segmentation_spleen"]["labels"] = {"liver": 2, "spleen": 1, "kidney": 3}
    info = monai_label.parse_info(data)
    assert info.models[0].labels == ("spleen", "liver", "kidney")


@pytest.mark.parametrize("missing", ["name", "version", "models", "trainers"])
def test_parse_info_rejects_missing_keys(missing):
    data = load_fixture("info_radiology_no_trainers.json")
    del data[missing]
    with pytest.raises(monai_label.InfoFormatError, match=missing):
        monai_label.parse_info(data)


@pytest.mark.parametrize("payload", [[], "ok", None, 42])
def test_parse_info_rejects_non_objects(payload):
    with pytest.raises(monai_label.InfoFormatError):
        monai_label.parse_info(payload)


def test_parse_info_rejects_models_not_object():
    data = load_fixture("info_radiology_no_trainers.json")
    data["models"] = ["segmentation_spleen"]
    with pytest.raises(monai_label.InfoFormatError, match="models"):
        monai_label.parse_info(data)


def test_format_info_mentions_app_models_and_missing_trainers():
    text = monai_label.format_info(monai_label.parse_info(load_fixture("info_radiology_no_trainers.json")))
    assert "App: MONAILabel - Radiology (0.8.6)" in text
    assert "  - segmentation_spleen (segmentation, 3D): spleen" in text
    assert "  - Histogram+GraphCut (scribbles, 3D)" in text
    assert "Trainers: none (training is not available on this server)" in text
    assert "Datastore: 78 images, 0 labelled" in text


def test_format_info_lists_trainers():
    text = monai_label.format_info(monai_label.parse_info(load_fixture("info_radiology_with_trainer.json")))
    assert "Trainers (1):\n  - segmentation_spleen" in text


# --- fetch_info against a local HTTP server ---------------------------------


class _Handler(http.server.BaseHTTPRequestHandler):
    # Set per test: (status, content type, body bytes, delay seconds)
    reply = (200, "application/json", b"{}", 0.0)
    paths = []

    def do_GET(self):
        type(self).paths.append(self.path)
        status, content_type, body, delay = type(self).reply
        if delay:
            time.sleep(delay)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@pytest.fixture
def server():
    _Handler.paths = []
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    httpd.daemon_threads = True
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def _reply(status=200, body=b"{}", content_type="application/json", delay=0.0):
    _Handler.reply = (status, content_type, body, delay)


def test_fetch_info_calls_info_with_trailing_slash(server):
    _, url = server
    _reply(body=(FIXTURES / "info_radiology_no_trainers.json").read_bytes())
    info = monai_label.fetch_info(url + "/")
    assert _Handler.paths == ["/info/"]
    assert info.name == "MONAILabel - Radiology (0.8.6)"
    assert info.trainers == ()


def test_fetch_info_reports_auth_required(server):
    _, url = server
    _reply(status=401, body=b'{"detail":"Not authenticated"}')
    with pytest.raises(monai_label.MonaiLabelServerError, match="requires authentication"):
        monai_label.fetch_info(url)


def test_fetch_info_reports_not_found(server):
    _, url = server
    _reply(status=404, body=b'{"detail":"Not Found"}')
    with pytest.raises(monai_label.MonaiLabelServerError, match="HTTP 404"):
        monai_label.fetch_info(url)


def test_fetch_info_reports_server_error(server):
    _, url = server
    _reply(status=500, body=b"boom", content_type="text/plain")
    with pytest.raises(monai_label.MonaiLabelServerError, match="HTTP 500"):
        monai_label.fetch_info(url)


def test_fetch_info_rejects_non_json(server):
    _, url = server
    _reply(body=b"<html>not monai</html>", content_type="text/html")
    with pytest.raises(monai_label.InfoFormatError, match="JSON"):
        monai_label.fetch_info(url)


def test_fetch_info_rejects_other_json(server):
    _, url = server
    _reply(body=b'{"status": "ok"}')
    with pytest.raises(monai_label.InfoFormatError, match="not a MONAI Label"):
        monai_label.fetch_info(url)


def test_fetch_info_times_out(server):
    _, url = server
    _reply(body=b"{}", delay=2.0)
    start = time.monotonic()
    with pytest.raises(monai_label.MonaiLabelConnectionError, match="No answer"):
        monai_label.fetch_info(url, timeout=0.5)
    assert time.monotonic() - start < 1.9


def _unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_fetch_info_reports_connection_refused():
    start = time.monotonic()
    with pytest.raises(monai_label.MonaiLabelConnectionError, match="connection refused"):
        monai_label.fetch_info(f"http://127.0.0.1:{_unused_port()}", timeout=5)
    assert time.monotonic() - start < 5


def test_fetch_info_reports_unknown_host():
    with pytest.raises(monai_label.MonaiLabelConnectionError):
        monai_label.fetch_info("http://monai-label.invalid:8000", timeout=5)


def test_fetch_info_rejects_bad_url_before_connecting():
    with pytest.raises(monai_label.UrlError):
        monai_label.fetch_info("localhost:8000")
