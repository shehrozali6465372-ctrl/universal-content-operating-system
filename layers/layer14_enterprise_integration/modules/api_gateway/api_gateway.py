"""APIGateway — Universal REST API for the AI Operating System.

Provides HTTP endpoints for:
- Content generation
- Pipeline execution
- Analytics retrieval
- System status
- Health checks

Uses only stdlib (http.server + json) — no external dependencies.

Endpoints:
    GET  /status          → System status
    GET  /health          → Health check
    GET  /analytics       → Analytics summary
    GET  /history         → Content history
    GET  /stats           → Full system stats
    POST /generate        → Generate content via pipeline
    GET  /templates       → Template rankings
    GET  /platforms       → Supported platforms
"""
from __future__ import annotations
import json
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs


class APIResponse:
    """Structured API response."""

    __slots__ = ("status_code", "data", "error", "headers")

    def __init__(self, status_code: int = 200, data: Any = None,
                 error: str = "") -> None:
        self.status_code = status_code
        self.data = data
        self.error = error
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "X-Powered-By": "Universal-AI-OS",
        }

    def to_json(self) -> str:
        body = {
            "success": self.status_code < 400,
            "status": self.status_code,
        }
        if self.data is not None:
            body["data"] = self.data
        if self.error:
            body["error"] = self.error
        body["timestamp"] = time.time()
        return json.dumps(body, indent=2, default=str)


class APIGateway:
    """Universal REST API Gateway for the AI OS."""

    SUPPORTED_PLATFORMS = [
        "facebook", "instagram", "linkedin", "twitter",
        "youtube", "tiktok", "pinterest", "threads",
        "medium", "wordpress", "telegram", "discord",
        "reddit", "binance_square",
    ]

    def __init__(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        self._host = host
        self._port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._request_count = 0
        self._routes: Dict[str, Any] = {}
        self._register_routes()

    def _register_routes(self) -> None:
        self._routes = {
            "GET /status": self._handle_status,
            "GET /health": self._handle_health,
            "GET /analytics": self._handle_analytics,
            "GET /history": self._handle_history,
            "GET /stats": self._handle_stats,
            "POST /generate": self._handle_generate,
            "GET /templates": self._handle_templates,
            "GET /platforms": self._handle_platforms,
        }

    def start(self) -> None:
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                gateway._request_count += 1
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/")
                params = parse_qs(parsed.query)
                route_key = f"GET {path}"

                if route_key in gateway._routes:
                    response = gateway._routes[route_key](params)
                else:
                    response = APIResponse(404, error=f"Endpoint not found: {path}")

                self.send_response(response.status_code)
                for key, val in response.headers.items():
                    self.send_header(key, val)
                self.end_headers()
                self.wfile.write(response.to_json().encode("utf-8"))

            def do_POST(self):
                gateway._request_count += 1
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/")
                route_key = f"POST {path}"

                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length) if content_length > 0 else b""

                try:
                    data = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    data = {}

                if route_key in gateway._routes:
                    response = gateway._routes[route_key](data)
                else:
                    response = APIResponse(404, error=f"Endpoint not found: {path}")

                self.send_response(response.status_code)
                for key, val in response.headers.items():
                    self.send_header(key, val)
                self.end_headers()
                self.wfile.write(response.to_json().encode("utf-8"))

            def log_message(self, format, *args):
                pass

        try:
            self._server = HTTPServer((self._host, self._port), Handler)
            self._running = True
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
        except OSError as exc:
            print(f"⚠️  API Gateway failed to start on {self._host}:{self._port}: {exc}")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._running = False

    def is_running(self) -> bool:
        return self._running

    def _handle_status(self, params: Dict) -> APIResponse:
        try:
            import glob
            layer_dirs = sorted(glob.glob("layers/layer*/"))
            return APIResponse(data={
                "version": "5.8.0",
                "status": "running",
                "layers": len(layer_dirs),
                "gateway_requests": self._request_count,
                "platforms": self.SUPPORTED_PLATFORMS,
            })
        except Exception as exc:
            return APIResponse(500, error=str(exc))

    def _handle_health(self, params: Dict) -> APIResponse:
        checks = {"api": "healthy", "database": "unknown"}
        try:
            from layers.layer01_core.modules.database_manager import DatabaseManager
            db = DatabaseManager()
            db.initialize()
            db.health_check()
            checks["database"] = "healthy"
            db.close()
        except Exception:
            checks["database"] = "unavailable"
        k1 = os.environ.get("GEMINI_API_KEY_1", "")
        checks["gemini"] = "configured" if k1 else "not_configured"
        overall = "healthy" if all(v in ("healthy", "configured", "not_configured") for v in checks.values()) else "degraded"
        return APIResponse(data={"status": overall, "checks": checks})

    def _handle_analytics(self, params: Dict) -> APIResponse:
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
            persist = PipelinePersistence()
            summary = persist.get_analytics_summary()
            persist.close()
            return APIResponse(data={"analytics": summary})
        except Exception as exc:
            return APIResponse(500, error=str(exc))

    def _handle_history(self, params: Dict) -> APIResponse:
        try:
            limit = int(params.get("limit", [10])[0])
            platform = params.get("platform", [None])[0]
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
            persist = PipelinePersistence()
            history = persist.get_content_history(platform=platform, limit=limit)
            persist.close()
            return APIResponse(data={"history": history, "count": len(history)})
        except Exception as exc:
            return APIResponse(500, error=str(exc))

    def _handle_stats(self, params: Dict) -> APIResponse:
        try:
            import glob
            layer_dirs = sorted(glob.glob("layers/layer*/"))
            total_files = sum(len(glob.glob(f"{d}**/*.py", recursive=True)) for d in layer_dirs)
            test_files = len(glob.glob("tests/**/test_*.py", recursive=True))
            db_stats = {}
            try:
                from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
                persist = PipelinePersistence()
                db_stats = persist.get_db_stats()
                persist.close()
            except Exception:
                pass
            return APIResponse(data={
                "version": "5.8.0", "layers": len(layer_dirs),
                "source_files": total_files, "test_files": test_files,
                "database": db_stats,
            })
        except Exception as exc:
            return APIResponse(500, error=str(exc))

    def _handle_generate(self, data: Dict) -> APIResponse:
        topic = data.get("topic", "artificial intelligence")
        platform = data.get("platform", "facebook")
        tone = data.get("tone", "professional")
        style = data.get("style", "educational")
        include_image = data.get("include_image", True)
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
                PipelineWiring, ContentRequest,
            )
            pipe = PipelineWiring()
            req = ContentRequest(topic=topic, platform=platform, tone=tone,
                style=style, include_image=include_image)
            response = pipe.execute(req)
            return APIResponse(data=response.to_dict())
        except Exception as exc:
            return APIResponse(500, error=str(exc))

    def _handle_templates(self, params: Dict) -> APIResponse:
        try:
            from layers.layer09_learning.modules.prompt_evolution.template_ranker import TemplateRanker
            ranker = TemplateRanker()
            platform = params.get("platform", [None])[0]
            rankings = ranker.get_rankings(platform=platform)
            return APIResponse(data={"rankings": rankings, "count": len(rankings)})
        except Exception as exc:
            return APIResponse(500, error=str(exc))

    def _handle_platforms(self, params: Dict) -> APIResponse:
        return APIResponse(data={
            "platforms": self.SUPPORTED_PLATFORMS,
            "publishers": {
                "facebook": "implemented",
                "instagram": "implemented",
                "linkedin": "implemented",
            },
        })
