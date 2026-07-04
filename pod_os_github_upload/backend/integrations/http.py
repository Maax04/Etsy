from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class IntegrationError(RuntimeError):
    pass


def request_json(method: str, url: str, *, headers: dict[str, str] | None = None, data: dict | None = None, form: dict | None = None, timeout: int = 60) -> dict:
    body = None
    final_headers = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        final_headers["Content-Type"] = "application/json"
    elif form is not None:
        body = urlencode(form).encode("utf-8")
        final_headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = Request(url, data=body, headers=final_headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise IntegrationError(f"{method} {url} failed with {exc.code}: {detail}") from exc
    except URLError as exc:
        raise IntegrationError(f"{method} {url} failed: {exc.reason}") from exc
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def request_multipart(method: str, url: str, *, headers: dict[str, str], fields: dict[str, str], files: dict[str, Path], timeout: int = 60) -> dict:
    boundary = f"----pod-os-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    for name, path in files.items():
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode("utf-8"))
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    final_headers = dict(headers)
    final_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    final_headers["Content-Length"] = str(len(body))
    req = Request(url, data=body, headers=final_headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise IntegrationError(f"{method} {url} failed with {exc.code}: {detail}") from exc
    except URLError as exc:
        raise IntegrationError(f"{method} {url} failed: {exc.reason}") from exc
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))
