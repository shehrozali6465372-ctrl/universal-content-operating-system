"""UCOS Personal Browser worker.

A bounded, authenticated Playwright browser worker for UCOS. It executes
explicit navigation/extraction actions and returns structured evidence.
It does not accept credentials, arbitrary JavaScript, file uploads, or
CAPTCHA/anti-bot bypass instructions.
"""
from __future__ import annotations

import atexit
import ipaddress
import json
import logging
import os
import socket
import time
import threading
import re
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


LOG = logging.getLogger("ucos.browser")
MAX_ACTIONS = 20
MAX_TEXT = 200_000
MAX_LINKS = 2_000
DEFAULT_TIMEOUT_MS = 30_000
_BROWSER_SLOTS = threading.BoundedSemaphore(1)
_SESSION_LOCK = threading.RLock()
_BROWSER_RUNTIME = None
SESSION_IDLE_TTL_SECONDS = 15 * 60


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


def _resolve_form_selector(page, selector: str):
    """Resolve a user-supplied form locator without masking Playwright errors."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    requested = selector.strip()
    if not requested or len(requested) > 500:
        raise ValueError("selector is required and must be <= 500 chars")

    # Keep the caller's selector first, then use stable semantic fallbacks for
    # known login controls. No CAPTCHA or anti-bot control is bypassed.
    candidates = [(requested, page.locator(requested).first)]
    if requested == "#ap_email":
        candidates += [
            ("input#ap_email", page.locator("input#ap_email").first),
            ("input[name='email']", page.locator("input[name='email']").first),
            ("input[type='email']", page.locator("input[type='email']").first),
            ("label:has-text('Email')", page.get_by_label(re.compile(r"email", re.I)).first),
        ]
    elif requested == "#ap_password":
        candidates += [
            ("input#ap_password", page.locator("input#ap_password").first),
            ("input[name='password']", page.locator("input[name='password']").first),
            ("input[type='password']", page.locator("input[type='password']").first),
            ("label:has-text('Password')", page.get_by_label(re.compile(r"password", re.I)).first),
        ]
    elif requested == "#signInSubmit":
        candidates += [
            ("input#signInSubmit", page.locator("input#signInSubmit").first),
            ("button#signInSubmit", page.locator("button#signInSubmit").first),
            ("input[type='submit']", page.locator("input[type='submit']").first),
            ("button[type='submit']", page.locator("button[type='submit']").first),
        ]

    last_error = None
    for candidate, locator in candidates:
        try:
            locator.wait_for(state="visible", timeout=3_000)
            return locator, candidate
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            last_error = exc
            continue

    raise ValueError(
        f"selector not found or not visible on current page: {requested}; "
        "use Inspect to identify the current form control"
    ) from last_error


def _profile_ref(value: str) -> str:
    ref = re.sub(r"[^A-Za-z0-9._-]", "-", str(value or "").strip())
    if not ref or len(ref) > 80:
        raise ValueError("profile_ref must be 1..80 safe characters")
    return ref


def _profile_dir(profile_ref: str) -> tuple[str, bool]:
    configured = os.getenv("UCOS_BROWSER_PROFILE_DIR", "").strip()
    root = Path(configured or "/var/data/ucos-browser/profiles")
    path = root / _profile_ref(profile_ref)
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return str(path), True
    except OSError as exc:
        if configured:
            raise RuntimeError("configured browser profile directory is not writable") from exc
        fallback = Path("/tmp/ucos-browser/profiles") / _profile_ref(profile_ref)
        fallback.mkdir(parents=True, exist_ok=True)
        LOG.warning("browser profile storage %s is not writable; using ephemeral fallback %s", root, fallback)
        return str(fallback), False


def _close_browser_runtime_locked() -> None:
    global _BROWSER_RUNTIME
    runtime = _BROWSER_RUNTIME
    _BROWSER_RUNTIME = None
    if not runtime:
        return
    try:
        runtime["context"].close()
    except Exception:
        LOG.exception("failed to close browser context")
    try:
        runtime["pw"].stop()
    except Exception:
        LOG.exception("failed to stop Playwright runtime")


def _close_browser_runtime() -> None:
    with _SESSION_LOCK:
        _close_browser_runtime_locked()


def _get_browser_runtime(profile_ref: str, timeout: int) -> tuple[dict, bool]:
    global _BROWSER_RUNTIME
    now = time.monotonic()
    with _SESSION_LOCK:
        runtime = _BROWSER_RUNTIME
        if runtime and (
            runtime["profile_ref"] != profile_ref
            or now - runtime["last_used"] > SESSION_IDLE_TTL_SECONDS
        ):
            _close_browser_runtime_locked()
            runtime = None

        if runtime:
            page = runtime["page"]
            if page.is_closed():
                page = runtime["context"].new_page()
                runtime["page"] = page
            page.set_default_timeout(timeout)
            runtime["last_used"] = now
            return runtime, False

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is required by the UCOS Personal Browser worker") from exc

        profile_dir, persistent_profile = _profile_dir(profile_ref)
        pw = sync_playwright().start()
        try:
            context = pw.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-zygote"],
                ignore_https_errors=False,
                accept_downloads=False,
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(timeout)
        except Exception:
            try:
                pw.stop()
            except Exception:
                LOG.exception("failed to stop Playwright after launch failure")
            raise

        runtime = {
            "profile_ref": profile_ref,
            "persistent_profile": persistent_profile,
            "profile_dir": profile_dir,
            "pw": pw,
            "context": context,
            "page": page,
            "last_used": now,
        }
        _BROWSER_RUNTIME = runtime
        return runtime, True


atexit.register(_close_browser_runtime)


def execute_task(task: dict) -> dict:
    requested_url = str(task.get("url", "")).strip()
    url = validate_url(requested_url) if requested_url else ""
    profile_ref = _profile_ref(task.get("profile_ref", "default"))
    actions = task.get("actions") or [{"type": "extract"}]
    if not isinstance(actions, list) or len(actions) > MAX_ACTIONS:
        raise ValueError(f"actions must be a list of at most {MAX_ACTIONS} items")
    timeout = max(1_000, min(int(task.get("timeout_ms", DEFAULT_TIMEOUT_MS)), 60_000))
    started = time.monotonic()
    result = {"url": url, "title": "", "text": "", "links": [], "screenshot": None, "events": []}
    if not _BROWSER_SLOTS.acquire(blocking=False):
        raise RuntimeError("browser worker is busy; retry the task")
    try:
        runtime, created = _get_browser_runtime(profile_ref, timeout)
        page = runtime["page"]
        explicit_navigation = any(
            str(action.get("type", "")).strip().lower() == "navigate"
            for action in actions
            if isinstance(action, dict)
        )
        if created and url and not explicit_navigation:
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            _assert_public_page(page)
            result["events"].append({
                "type": "navigate",
                "status": response.status if response else None,
                "url": page.url,
                "reason": "session_init",
            })

        for action in actions:
            kind = str(action.get("type", "")).strip().lower()
            if kind == "navigate":
                target = validate_url(action.get("url", ""))
                response = page.goto(target, wait_until="domcontentloaded", timeout=timeout)
                _assert_public_page(page)
                result["events"].append({
                    "type": "navigate",
                    "status": response.status if response else None,
                    "url": page.url,
                })
            elif kind == "click":
                selector = str(action.get("selector", "")).strip()
                if not selector or len(selector) > 500:
                    raise ValueError("click selector is required and must be <= 500 chars")
                locator, resolved_selector = _resolve_form_selector(page, selector)
                locator.click()
                _assert_public_page(page)
                result["events"].append({"type": "click", "selector": resolved_selector})
            elif kind == "wait":
                ms = max(0, min(int(action.get("ms", 250)), 10_000))
                page.wait_for_timeout(ms)
            elif kind == "press":
                selector = str(action.get("selector", "")).strip()
                key = str(action.get("key", "")).strip()
                if not selector or not key or len(key) > 100:
                    raise ValueError("press requires selector and key")
                locator, resolved_selector = _resolve_form_selector(page, selector)
                locator.press(key)
                _assert_public_page(page)
                result["events"].append({
                    "type": "press",
                    "selector": resolved_selector,
                    "key": key,
                })
            elif kind == "fill":
                selector = str(action.get("selector", "")).strip()
                value = str(action.get("value", ""))
                if not selector or len(selector) > 500 or len(value) > 10_000:
                    raise ValueError("fill requires a valid selector and value <= 10000 chars")
                locator, resolved_selector = _resolve_form_selector(page, selector)
                locator.fill(value)
                _assert_public_page(page)
                result["events"].append({"type": "fill", "selector": resolved_selector})
            elif kind == "inspect":
                result["elements"] = page.locator("input,button,textarea,select,[role='button'],a").evaluate_all(
                    """els => els.slice(0, 200).map((e, i) => {
                        const out = {index:i, tag:e.tagName.toLowerCase(), text:(e.innerText||e.value||'').trim().slice(0,200)};
                        for (const a of ['id','name','type','aria-label','placeholder','role']) if (e.getAttribute(a)) out[a]=e.getAttribute(a);
                        if (e.id && /^[A-Za-z_][A-Za-z0-9_-]*$/.test(e.id)) out.selector='#'+e.id;
                        else if (e.name && /^[A-Za-z_][A-Za-z0-9_-]*$/.test(e.name)) out.selector=e.tagName.toLowerCase()+'[name="'+e.name+'"]';
                        return out;
                    })"""
                )
                result["title"] = page.title()[:500]
                result["final_url"] = page.url
            elif kind == "extract":
                text_value = page.locator("body").inner_text(timeout=timeout)
                result["text"] = text_value[:MAX_TEXT]
                result["title"] = page.title()[:500]
                hrefs = page.locator("a[href]").evaluate_all(
                    """els => els.slice(0, 2000).map(e => ({
                        text:(e.innerText||'').trim(),
                        href:e.href
                    }))"""
                )
                result["links"] = hrefs
            elif kind == "extract_selector":
                selector = str(action.get("selector", "")).strip()
                if not selector or len(selector) > 500:
                    raise ValueError("extract_selector selector is required and must be <= 500 chars")
                result["text"] = page.locator(selector).first.inner_text(timeout=timeout)[:MAX_TEXT]
            elif kind == "screenshot":
                result["screenshot"] = page.screenshot(type="png", full_page=False).hex()
            else:
                raise ValueError(f"unsupported browser action: {kind}")

        runtime["last_used"] = time.monotonic()
        result["profile_ref"] = profile_ref
        result["persistent_profile"] = runtime["persistent_profile"]
        result["session_reused"] = not created
        result["final_url"] = page.url
        result["url"] = page.url
        result["duration_ms"] = int((time.monotonic() - started) * 1000)
        return result
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

    def do_HEAD(self):
        if self.path.rstrip("/") in {"", "/health"}:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_console(self):
        try:
            raw = Path(__file__).with_name("console.html").read_bytes()
        except OSError:
            self._send(500, {"error": "console unavailable"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/session/health"):
            if not _authorized(self.headers):
                self._send(401, {"error": "authentication required"})
                return
            from urllib.parse import parse_qs
            query = parse_qs(urlsplit(self.path).query)
            profile_ref = query.get("profile_ref", ["default"])[0]
            try:
                path, persistent_profile = _profile_dir(profile_ref)
                has_state = any(Path(path).iterdir())
            except (OSError, ValueError, RuntimeError):
                has_state = False
                persistent_profile = False
            self._send(200, {
                "status": "ok",
                "profile_ref": _profile_ref(profile_ref),
                "persistent": persistent_profile,
                "profile_initialized": has_state,
                "authentication": "UNKNOWN",
            })
            return
        if self.path.rstrip("/") == "":
            self._serve_console()
            return
        if self.path.rstrip("/") == "/console":
            self._serve_console()
            return
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
