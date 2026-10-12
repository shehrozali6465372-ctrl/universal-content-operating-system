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
import uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

try:
    from . import profile_persistence
except ImportError:  # direct execution or tests importing server.py by file path
    try:
        import profile_persistence
    except ImportError:
        import importlib.util
        _profile_module_path = Path(__file__).with_name("profile_persistence.py")
        _profile_spec = importlib.util.spec_from_file_location(
            "ucos_browser_profile_persistence", _profile_module_path
        )
        if _profile_spec is None or _profile_spec.loader is None:
            raise RuntimeError("UCOS browser profile persistence module is unavailable")
        profile_persistence = importlib.util.module_from_spec(_profile_spec)
        _profile_spec.loader.exec_module(profile_persistence)


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
    durable_required = profile_persistence.durable_required()
    state_store_configured = profile_persistence.is_configured()
    if durable_required and not configured and not state_store_configured:
        raise RuntimeError(
            "durable browser profile storage is required; configure UCOS_BROWSER_PROFILE_DIR "
            "to a persistent volume or set DATABASE_URL and UCOS_BROWSER_STATE_ENCRYPTION_KEY"
        )
    root = Path(configured or "/var/data/ucos-browser/profiles")
    path = root / _profile_ref(profile_ref)
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        # A writable default path does not prove that Render mounted durable storage.
        return str(path), bool(configured)
    except OSError as exc:
        if configured:
            raise RuntimeError("configured browser profile directory is not writable") from exc
        if durable_required and not state_store_configured:
            raise RuntimeError(
                "durable browser profile storage is required; configure UCOS_BROWSER_PROFILE_DIR "
                "to a persistent volume or set DATABASE_URL and UCOS_BROWSER_STATE_ENCRYPTION_KEY"
            ) from exc
        fallback = Path("/tmp/ucos-browser/profiles") / _profile_ref(profile_ref)
        fallback.mkdir(parents=True, exist_ok=True)
        if state_store_configured:
            LOG.info(
                "local Chromium profile path %s is not writable; using ephemeral runtime profile %s "
                "with encrypted Postgres session snapshots",
                root,
                fallback,
            )
        else:
            LOG.warning(
                "browser profile storage %s is not writable; using ephemeral fallback %s",
                root,
                fallback,
            )
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

        profile_dir, disk_persistent = _profile_dir(profile_ref)
        state_store_enabled = profile_persistence.is_configured()
        saved_state = profile_persistence.load_profile_state(profile_ref) if state_store_enabled else None
        pw = sync_playwright().start()
        try:
            context = pw.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-zygote"],
                ignore_https_errors=False,
                accept_downloads=False,
            )
            if saved_state:
                profile_persistence.restore_storage_state(context, saved_state)
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
            "disk_persistent": disk_persistent,
            "state_store_enabled": state_store_enabled,
            "persistent_profile": bool(disk_persistent or state_store_enabled),
            "profile_persistence_backend": (
                "neon_postgres" if state_store_enabled and not disk_persistent
                else "disk+neon_postgres" if state_store_enabled
                else "disk" if disk_persistent
                else "ephemeral"
            ),
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
            elif kind in {"back", "forward", "reload"}:
                if kind == "back":
                    response = page.go_back(wait_until="domcontentloaded", timeout=timeout)
                elif kind == "forward":
                    response = page.go_forward(wait_until="domcontentloaded", timeout=timeout)
                else:
                    response = page.reload(wait_until="domcontentloaded", timeout=timeout)
                _assert_public_page(page)
                result["events"].append({
                    "type": kind,
                    "status": response.status if response else None,
                    "url": page.url,
                })
            elif kind == "new_tab":
                if len(runtime["context"].pages) >= 10:
                    raise ValueError("maximum of 10 tabs per profile reached")
                page = runtime["context"].new_page()
                page.set_default_timeout(timeout)
                runtime["page"] = page
                target = str(action.get("url", "")).strip()
                if target:
                    response = page.goto(validate_url(target), wait_until="domcontentloaded", timeout=timeout)
                    _assert_public_page(page)
                result["events"].append({"type": "new_tab", "url": page.url})
            elif kind == "switch_tab":
                try:
                    index = int(action.get("index", -1))
                except (TypeError, ValueError):
                    raise ValueError("tab index must be an integer")
                pages = [p for p in runtime["context"].pages if not p.is_closed()]
                if index < 0 or index >= len(pages):
                    raise ValueError(f"tab index out of range; open tabs: 0..{max(0, len(pages)-1)}")
                page = pages[index]
                page.set_default_timeout(timeout)
                runtime["page"] = page
                result["events"].append({"type": "switch_tab", "index": index, "url": page.url})
            elif kind == "close_tab":
                pages = [p for p in runtime["context"].pages if not p.is_closed()]
                if len(pages) <= 1:
                    raise ValueError("cannot close the last open tab")
                page.close()
                pages = [p for p in runtime["context"].pages if not p.is_closed()]
                runtime["page"] = pages[-1]
                page = runtime["page"]
                result["events"].append({"type": "close_tab", "url": page.url})
            elif kind == "list_tabs":
                pages = [p for p in runtime["context"].pages if not p.is_closed()]
                result["tabs"] = [{"index": i, "url": p.url, "title": p.title()[:160], "active": p == page} for i, p in enumerate(pages)]
                result["events"].append({"type": "list_tabs", "count": len(pages)})
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
        if runtime["state_store_enabled"]:
            try:
                profile_persistence.save_profile_state(
                    profile_ref, runtime["context"].storage_state()
                )
            except Exception as exc:
                if runtime["disk_persistent"]:
                    LOG.warning(
                        "encrypted browser profile snapshot failed; continuing with durable disk (%s)",
                        type(exc).__name__,
                    )
                else:
                    raise RuntimeError(
                        "browser session state could not be persisted; profile durability is unconfirmed"
                    ) from exc
        result["profile_ref"] = profile_ref
        result["persistent_profile"] = runtime["persistent_profile"]
        result["profile_persistence_backend"] = runtime["profile_persistence_backend"]
        result["session_reused"] = not created
        result["final_url"] = page.url
        result["url"] = page.url
        result["duration_ms"] = int((time.monotonic() - started) * 1000)
        return result
    finally:
        _BROWSER_SLOTS.release()


def _record_task_run(task_id: str, task: dict, state: str, result=None, error=None, duration_ms=None) -> None:
    """Persist minimal browser task audit metadata; never store page text, screenshots, cookies, or credentials."""
    dsn = (
        os.getenv("UCOS_BROWSER_STATE_DATABASE_URL", "").strip()
        or os.getenv("DATABASE_URL", "").strip()
    )
    if not dsn:
        return
    try:
        import psycopg
        requested_host = urlsplit(str(task.get("url", "") or "")).hostname
        final_host = urlsplit(str((result or {}).get("final_url", "") or "")).hostname
        profile_ref = _profile_ref(task.get("profile_ref", "default"))
        persistent_profile = (result or {}).get("persistent_profile")
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS browser_task_runs (
                        task_id TEXT PRIMARY KEY,
                        profile_ref TEXT NOT NULL,
                        requested_host TEXT,
                        final_host TEXT,
                        state TEXT NOT NULL CHECK (state IN ('completed', 'rejected', 'failed')),
                        duration_ms INTEGER,
                        persistent_profile BOOLEAN,
                        error_type TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    INSERT INTO browser_task_runs
                        (task_id, profile_ref, requested_host, final_host, state,
                         duration_ms, persistent_profile, error_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO NOTHING
                """, (
                    task_id, profile_ref, requested_host, final_host, state,
                    duration_ms, persistent_profile, type(error).__name__ if error else None,
                ))
    except Exception as exc:
        # Audit persistence must not expose DSNs or interrupt browser execution.
        LOG.warning("browser task audit write failed (%s)", type(exc).__name__)


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
            try:
                profile_ref = _profile_ref(query.get("profile_ref", ["default"])[0])
                path, disk_persistent = _profile_dir(profile_ref)
                # Chromium scratch files are not evidence of durable profile initialization.
                has_disk_state = disk_persistent and any(Path(path).iterdir())
                state_store_enabled = profile_persistence.is_configured()
                has_saved_state = (
                    profile_persistence.has_profile_state(profile_ref) if state_store_enabled else False
                )
                persistent_profile = bool(disk_persistent or state_store_enabled)
            except (OSError, ValueError, RuntimeError):
                self._send(400, {"error": "invalid or unavailable browser profile"})
                return
            backend = (
                "neon_postgres" if state_store_enabled and not disk_persistent
                else "disk+neon_postgres" if state_store_enabled
                else "disk" if disk_persistent
                else "ephemeral"
            )
            self._send(200, {
                "status": "ok",
                "profile_ref": profile_ref,
                "persistent": persistent_profile,
                "persistence_backend": backend,
                "profile_initialized": bool(has_disk_state or has_saved_state),
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
        task_id = uuid.uuid4().hex
        started = time.monotonic()
        payload = {}
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 1_000_000:
                raise ValueError("request body must be 1..1000000 bytes")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("request body must be an object")
            result = execute_task(payload)
            duration_ms = int((time.monotonic() - started) * 1000)
            _record_task_run(task_id, payload, "completed", result=result, duration_ms=duration_ms)
            self._send(200, {"state": "completed", "task_id": task_id, "result": result})
        except (ValueError, TypeError) as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            if isinstance(payload, dict):
                _record_task_run(task_id, payload, "rejected", error=exc, duration_ms=duration_ms)
            self._send(400, {"state": "rejected", "task_id": task_id, "error": str(exc)})
        except Exception as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            if isinstance(payload, dict):
                _record_task_run(task_id, payload, "failed", error=exc, duration_ms=duration_ms)
            LOG.exception("browser task failed")
            self._send(502, {"state": "failed", "task_id": task_id, "error": str(exc)[:1000]})

    def log_message(self, fmt, *args):
        LOG.info("%s - %s", self.address_string(), fmt % args)


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _run_profile_persistence_startup_self_test() -> None:
    durable_required = profile_persistence.durable_required()
    run_self_test = _env_enabled("UCOS_BROWSER_SESSION_SELF_TEST")

    if run_self_test:
        try:
            profile_persistence.self_test()
            LOG.info("UCOS_BROWSER_SESSION_PERSISTENCE_SELF_TEST=PASS backend=encrypted_postgres")
        except Exception as exc:
            LOG.error(
                "UCOS_BROWSER_SESSION_PERSISTENCE_SELF_TEST=FAIL error_type=%s",
                type(exc).__name__,
            )
            if durable_required:
                raise RuntimeError(
                    "durable browser profile storage is required but its startup self-test failed"
                ) from exc

    if not durable_required:
        return

    # The generic self-test proves the DB/key pair can round-trip a fresh snapshot.
    # Validate the real named profile too, without logging cookies, localStorage values,
    # or any other session content. This catches encryption-key drift after redeploys.
    profile_ref = _profile_ref(
        os.getenv("UCOS_BROWSER_PERSISTENCE_CHECK_PROFILE", "amazon-primary")
    )
    try:
        saved_state = profile_persistence.load_profile_state(profile_ref)
    except Exception as exc:
        LOG.error(
            "UCOS_BROWSER_EXISTING_PROFILE_SNAPSHOT=FAIL profile_ref=%s error_type=%s",
            profile_ref,
            type(exc).__name__,
        )
        raise RuntimeError(
            "durable browser profile storage is required but the saved profile could not be validated"
        ) from exc

    if saved_state is None:
        LOG.info(
            "UCOS_BROWSER_EXISTING_PROFILE_SNAPSHOT=NOT_FOUND profile_ref=%s",
            profile_ref,
        )
        return

    cookies = saved_state.get("cookies", [])
    origins = saved_state.get("origins", [])
    LOG.info(
        "UCOS_BROWSER_EXISTING_PROFILE_SNAPSHOT=DECRYPTABLE profile_ref=%s "
        "cookie_count=%d origin_count=%d",
        profile_ref,
        len(cookies) if isinstance(cookies, list) else 0,
        len(origins) if isinstance(origins, list) else 0,
    )


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    port = int(os.getenv("PORT", "10000"))
    if not os.getenv("UCOS_BROWSER_TOKEN", "").strip():
        raise RuntimeError("UCOS_BROWSER_TOKEN is required")
    _run_profile_persistence_startup_self_test()
    server = HTTPServer(("0.0.0.0", port), Handler)
    LOG.info("UCOS Personal Browser listening on 0.0.0.0:%s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
