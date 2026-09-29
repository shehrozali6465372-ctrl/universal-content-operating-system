"""UCOS Personal Browser worker.

A bounded, authenticated Playwright browser worker for UCOS. It executes
explicit navigation/extraction actions and returns structured evidence.
It does not accept credentials, arbitrary JavaScript, file uploads, or
CAPTCHA/anti-bot bypass instructions.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import os
import socket
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


LOG = logging.getLogger("ucos.browser")
MAX_ACTIONS = 20
MAX_TEXT = 200_000
MAX_LINKS = 2_000
DEFAULT_TIMEOUT_MS = 30_000
_BROWSER_SLOTS = threading.BoundedSemaphore(1)


def _is_public_host(hostname: str) -> bool:
    host = hostname.strip("[]").lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        return False
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("target host could not be resolved") from exc
    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if addr.is_loopback or addr.is_private or addr.is_link_local or addr.is_reserved or addr.is_multicast:
            return False
    return True


def validate_url(value: str) -> str:
    url = str(value or "").strip()
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("url must be an absolute HTTP(S) URL")
    if not _is_public_host(parsed.hostname):
        raise ValueError("private or local network targets are blocked")
    return url


def _assert_public_page(page) -> None:
    validate_url(page.url)


def execute_task(task: dict) -> dict:
    url = validate_url(task.get("url", ""))
    actions = task.get("actions") or [{"type": "extract"}]
    if not isinstance(actions, list) or len(actions) > MAX_ACTIONS:
        raise ValueError(f"actions must be a list of at most {MAX_ACTIONS} items")
    timeout = max(1_000, min(int(task.get("timeout_ms", DEFAULT_TIMEOUT_MS)), 60_000))
    started = time.monotonic()
    result = {"url": url, "title": "", "text": "", "links": [], "screenshot": None, "events": []}
    if not _BROWSER_SLOTS.acquire(blocking=False):
        raise RuntimeError("browser worker is busy; retry the task")
    try:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is required by the UCOS Personal Browser worker") from exc
        with sync_playwright() as pw:
            browser: Browser = pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-zygote", "--single-process"],
            )
            context = browser.new_context(ignore_https_errors=False, accept_downloads=False)
            page = context.new_page()
            page.set_default_timeout(timeout)
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                _assert_public_page(page)
                result["events"].append({"type": "navigate", "status": response.status if response else None, "url": page.url})
                for action in actions:
                    kind = str(action.get("type", "")).strip().lower()
                    if kind == "navigate":
                        target = validate_url(action.get("url", ""))
                        response = page.goto(target, wait_until="domcontentloaded", timeout=timeout)
                        _assert_public_page(page)
                        result["events"].append({"type": "navigate", "status": response.status if response else None, "url": page.url})
                    elif kind == "click":
                        selector = str(action.get("selector", "")).strip()
                        if not selector or len(selector) > 500:
                            raise ValueError("click selector is required and must be <= 500 chars")
                        page.locator(selector).first.click()
                        _assert_public_page(page)
                        result["events"].append({"type": "click", "selector": selector})
                    elif kind == "wait":
                        ms = max(0, min(int(action.get("ms", 250)), 10_000))
                        page.wait_for_timeout(ms)
                    elif kind == "press":
                        selector = str(action.get("selector", "")).strip()
                        key = str(action.get("key", "")).strip()
                        if not selector or not key or len(key) > 100:
                            raise ValueError("press requires selector and key")
                        page.locator(selector).first.press(key)
                        _assert_public_page(page)
                        result["events"].append({"type": "press", "selector": selector, "key": key})
                    elif kind == "extract":
                        text = page.locator("body").inner_text(timeout=timeout)
                        result["text"] = text[:MAX_TEXT]
                        result["title"] = page.title()[:500]
                        hrefs = page.locator("a[href]").evaluate_all(
                            "els => els.map(e => ({text:(e.innerText||'').trim(), href:e.href}))"
                        )
                        result["links"] = hrefs[:MAX_LINKS]
                    elif kind == "extract_selector":
                        selector = str(action.get("selector", "")).strip()
                        if not selector or len(selector) > 500:
                            raise ValueError("extract_selector selector is required and must be <= 500 chars")
                        result["text"] = page.locator(selector).first.inner_text(timeout=timeout)[:MAX_TEXT]
                    elif kind == "screenshot":
                        result["screenshot"] = page.screenshot(type="png", full_page=False).hex()
                    else:
                        raise ValueError(f"unsupported browser action: {kind}")
                result["final_url"] = page.url
                result["duration_ms"] = int((time.monotonic() - started) * 1000)
                return result
            finally:
                context.close()
                browser.close()
    finally:
        _BROWSER_SLOTS.release()
def _authorized(headers) -> bool:
    token = os.getenv("UCOS_BROWSER_TOKEN", "").strip()
    supplied = str(headers.get("Authorization", ""))
    return bool(token) and supplied == f"Bearer {token}"


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict) -> None:
        raw = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.rstrip("/") != "/health":
            self._send(404, {"error": "not found"})
            return
        if not _authorized(self.headers):
            self._send(401, {"error": "authentication required"})
            return
        self._send(200, {"status": "ok", "service": "ucos-personal-browser", "engine": "playwright-chromium"})

    def do_POST(self):
        if self.path.rstrip("/") != "/execute":
            self._send(404, {"error": "not found"})
            return
        if not _authorized(self.headers):
            self._send(401, {"error": "authentication required"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 1_000_000:
                raise ValueError("request body must be 1..1000000 bytes")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("request body must be an object")
            self._send(200, {"state": "completed", "result": execute_task(payload)})
        except (ValueError, TypeError) as exc:
            self._send(400, {"state": "rejected", "error": str(exc)})
        except Exception as exc:
            LOG.exception("browser task failed")
            self._send(502, {"state": "failed", "error": str(exc)[:1000]})

    def log_message(self, fmt, *args):
        LOG.info("%s - %s", self.address_string(), fmt % args)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    port = int(os.getenv("PORT", "10000"))
    if not os.getenv("UCOS_BROWSER_TOKEN", "").strip():
        raise RuntimeError("UCOS_BROWSER_TOKEN is required")
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    LOG.info("UCOS Personal Browser listening on 0.0.0.0:%s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
