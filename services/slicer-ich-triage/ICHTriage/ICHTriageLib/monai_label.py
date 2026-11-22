"""Minimal MONAI Label client: URL checks and the ``GET /info/`` call.

The response format follows the MONAI Label source at tag 0.8.6:

- ``monailabel/endpoints/info.py``: the route is ``GET /info/`` (with the
  trailing slash, as the MONAILabel Slicer extension calls it).
- ``monailabel/interfaces/app.py``, ``MONAILabelApp.info()``: top-level keys
  ``name``, ``description``, ``version``, ``labels``, ``models``,
  ``trainers``, ``strategies``, ``scoring``, ``train_stats``, ``datastore``.
- ``monailabel/tasks/infer/basic_infer.py``, ``BasicInferTask.info()``: each
  model has ``type``, ``labels``, ``dimension``, ``description``, ``config``.
- ``monailabel/interfaces/tasks/train.py``, ``TrainTask.info()``: each
  trainer has ``description`` and ``config``.

Only the standard library is used, so this module runs inside Slicer and under
pytest without extra packages.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

DEFAULT_SERVER_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 5.0
INFO_PATH = "/info/"

# A real /info/ response is a few kB; anything far larger is not MONAI Label.
_MAX_RESPONSE_BYTES = 10 * 1024 * 1024
_REQUIRED_INFO_KEYS = ("name", "version", "models", "trainers")


class UrlError(ValueError):
    """A URL typed by the user is not usable."""


class MonaiLabelError(Exception):
    """Base class for errors talking to a MONAI Label server.

    The message is meant to be shown to the user as is.
    """


class MonaiLabelConnectionError(MonaiLabelError):
    """The server could not be reached, or did not answer in time."""


class MonaiLabelServerError(MonaiLabelError):
    """The server answered with an HTTP error status."""


class InfoFormatError(MonaiLabelError):
    """The server answered, but not with a MONAI Label ``/info/`` payload."""


@dataclass(frozen=True)
class ModelInfo:
    name: str
    type: str
    dimension: int | None
    labels: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class TrainerInfo:
    name: str
    description: str


@dataclass(frozen=True)
class AppInfo:
    name: str
    version: str
    description: str
    labels: tuple[str, ...]
    models: tuple[ModelInfo, ...]
    trainers: tuple[TrainerInfo, ...]
    strategies: tuple[str, ...]
    datastore_total: int | None
    datastore_completed: int | None


def _check_http_url(text: str, what: str) -> str:
    parts = urllib.parse.urlsplit(text)
    if parts.scheme not in ("http", "https"):
        raise UrlError(f"{what} must start with http:// or https:// (got {text!r}).")
    if not parts.hostname:
        raise UrlError(f"{what} has no host name (got {text!r}).")
    if parts.username or parts.password:
        raise UrlError(f"{what} must not contain a user name or password.")
    if parts.query or parts.fragment:
        raise UrlError(f"{what} must not contain a query string or a fragment (got {text!r}).")
    try:
        parts.port
    except ValueError:
        raise UrlError(f"{what} has an invalid port (got {text!r}).") from None
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def normalize_server_url(url: str | None) -> str:
    """Check a MONAI Label server URL and return it without a trailing slash.

    Raises ``UrlError`` when the URL is empty or not an http(s) URL.
    """
    text = (url or "").strip()
    if not text:
        raise UrlError("MONAI Label server URL is empty.")
    return _check_http_url(text, "MONAI Label server URL")


def normalize_dicomweb_url(url: str | None) -> str:
    """Check a PACS DICOMweb root URL. An empty value is allowed and returns ``""``."""
    text = (url or "").strip()
    if not text:
        return ""
    return _check_http_url(text, "PACS DICOMweb URL")


def _label_names(labels: Any) -> tuple[str, ...]:
    # MONAI Label accepts labels as a list of names or as a {name: index} mapping.
    if isinstance(labels, Mapping):
        return tuple(str(name) for name, _ in sorted(labels.items(), key=lambda item: item[1]))
    if isinstance(labels, (list, tuple)):
        return tuple(str(name) for name in labels)
    if labels in (None, ""):
        return ()
    return (str(labels),)


def _mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise InfoFormatError(f"'{key}' in the /info/ response is not an object.")
    return value


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def parse_info(data: Any) -> AppInfo:
    """Turn a decoded ``/info/`` response into an ``AppInfo``.

    Raises ``InfoFormatError`` when the payload does not look like MONAI Label.
    """
    if not isinstance(data, Mapping):
        raise InfoFormatError("The /info/ response is not a JSON object.")
    missing = [key for key in _REQUIRED_INFO_KEYS if key not in data]
    if missing:
        raise InfoFormatError(
            "The server answered, but this is not a MONAI Label /info/ response "
            f"(missing: {', '.join(missing)})."
        )

    models = []
    for name, model in _mapping(data, "models").items():
        model = model if isinstance(model, Mapping) else {}
        models.append(
            ModelInfo(
                name=str(name),
                type=str(model.get("type") or ""),
                dimension=_optional_int(model.get("dimension")),
                labels=_label_names(model.get("labels")),
                description=str(model.get("description") or ""),
            )
        )

    trainers = []
    for name, trainer in _mapping(data, "trainers").items():
        trainer = trainer if isinstance(trainer, Mapping) else {}
        trainers.append(TrainerInfo(name=str(name), description=str(trainer.get("description") or "")))

    datastore = _mapping(data, "datastore")
    return AppInfo(
        name=str(data.get("name") or ""),
        version=str(data.get("version") or ""),
        description=str(data.get("description") or ""),
        labels=_label_names(data.get("labels")),
        models=tuple(models),
        trainers=tuple(trainers),
        strategies=tuple(str(name) for name in _mapping(data, "strategies")),
        datastore_total=_optional_int(datastore.get("total")),
        datastore_completed=_optional_int(datastore.get("completed")),
    )


def _is_timeout(error: BaseException) -> bool:
    return isinstance(error, (TimeoutError, socket.timeout))


def fetch_info(server_url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> AppInfo:
    """Call ``GET {server_url}/info/`` and parse the answer.

    The request does not go through system proxies, like the MONAILabel Slicer
    extension (it uses ``http.client`` directly). No credentials are sent.

    Raises ``UrlError`` for a bad URL and a ``MonaiLabelError`` subclass for
    every other failure, each with a message meant for the user.
    """
    base = normalize_server_url(server_url)
    url = base + INFO_PATH
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(_MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise MonaiLabelServerError(
                f"The MONAI Label server at {base} requires authentication (HTTP {error.code}). "
                "This module does not send credentials yet; use a server started without "
                "MONAI_LABEL_AUTH_ENABLE."
            ) from None
        if error.code == 404:
            raise MonaiLabelServerError(
                f"{url} was not found (HTTP 404). Check that the URL points to a MONAI Label server."
            ) from None
        raise MonaiLabelServerError(
            f"The MONAI Label server at {base} answered HTTP {error.code} {error.reason} to GET {INFO_PATH}."
        ) from None
    except urllib.error.URLError as error:
        reason = error.reason
        if _is_timeout(reason):
            message = f"No answer from {base} within {timeout:g} s. Is the MONAI Label server running?"
        elif isinstance(reason, ConnectionRefusedError):
            message = f"Cannot connect to {base}: connection refused. Is the MONAI Label server running?"
        elif isinstance(reason, socket.gaierror):
            message = f"Cannot resolve the host name in {base}."
        else:
            message = f"Cannot connect to {base}: {reason}."
        raise MonaiLabelConnectionError(message) from None
    except OSError as error:
        if _is_timeout(error):
            message = f"No answer from {base} within {timeout:g} s. Is the MONAI Label server running?"
        else:
            message = f"Connection to {base} failed: {error}."
        raise MonaiLabelConnectionError(message) from None

    if len(body) > _MAX_RESPONSE_BYTES:
        raise InfoFormatError(f"The /info/ response from {base} is too large to be MONAI Label.")
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise InfoFormatError(f"The server at {base} did not answer GET {INFO_PATH} with JSON.") from None
    return parse_info(data)


def format_info(info: AppInfo) -> str:
    """Plain-text summary of an ``AppInfo`` for the module panel."""
    lines = [f"App: {info.name or '(no name)'}"]
    if info.version:
        lines.append(f"Version: {info.version}")
    if info.description:
        lines.append(f"Description: {info.description}")

    lines.append(f"Models ({len(info.models)}):" if info.models else "Models: none")
    for model in info.models:
        kind = ", ".join(part for part in (model.type, f"{model.dimension}D" if model.dimension else "") if part)
        labels = f": {', '.join(model.labels)}" if model.labels else ""
        lines.append(f"  - {model.name}" + (f" ({kind})" if kind else "") + labels)

    if info.trainers:
        lines.append(f"Trainers ({len(info.trainers)}):")
        lines.extend(f"  - {trainer.name}" for trainer in info.trainers)
    else:
        lines.append("Trainers: none (training is not available on this server)")

    if info.datastore_total is not None:
        completed = info.datastore_completed if info.datastore_completed is not None else "?"
        lines.append(f"Datastore: {info.datastore_total} images, {completed} labelled")
    return "\n".join(lines)
