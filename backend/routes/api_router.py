"""
Modular HTTP REST API Router for RAINSHIELD-AI v6.0 (SIH26071)
Routes requests across GridController, AlertController (SMTP & Scheduler), and MLController (Dataset & DB).
"""
import http.server
import json
import urllib.parse
from typing import Any

from backend.config.settings import PROJECT_ROOT
from backend.controllers.grid_controller import grid_controller
from backend.controllers.alert_controller import alert_controller
from backend.controllers.ml_controller import ml_controller


class RainshieldRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/api/grids":
            self._send_json(grid_controller.get_grids_response())
            return

        if path == "/api/backtests":
            self._send_json(grid_controller.get_backtests_response())
            return

        if path == "/api/audit":
            self._send_json(alert_controller.get_audit_logs_response())
            return

        if path == "/api/simulate":
            rain = float(qs.get("rain", [79.4])[0])
            cn = float(qs.get("cn", [91.0])[0])
            drainage = float(qs.get("drainage", [58.0])[0])
            self._send_json(grid_controller.simulate_physics(rain, cn, drainage))
            return

        if path.startswith("/api/cctv/"):
            grid_id = path.split("/api/cctv/")[1]
            self._send_json(grid_controller.get_cctv_gauge(grid_id))
            return

        if path.startswith("/api/cap/"):
            grid_id = path.split("/api/cap/")[1]
            xml_str, resolved_id = alert_controller.get_cap_xml_response(grid_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="CAP_v1.2_{resolved_id}.xml"')
            self.end_headers()
            self.wfile.write(xml_str.encode("utf-8"))
            return

        if path == "/api/alerts/emails" or path == "/api/scheduler/status":
            self._send_json(alert_controller.get_email_and_scheduler_dashboard())
            return

        if path == "/api/ml/overview" or path == "/api/db/overview":
            self._send_json(ml_controller.get_ml_and_db_dashboard())
            return

        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body)
        except Exception:
            body = {}

        if path == "/api/alerts/transmit":
            self._send_json(alert_controller.handle_alert_transmission(body))
            return

        if path == "/api/override":
            self._send_json(alert_controller.handle_hitl_override(body))
            return

        if path == "/api/scada":
            self._send_json(grid_controller.handle_scada_control(body))
            return

        if path == "/api/ml/retrain":
            self._send_json(ml_controller.trigger_retrain())
            return

        if path == "/api/ml/predict":
            self._send_json(ml_controller.predict_custom(body))
            return

        self._send_json({"error": "Unknown POST endpoint"}, status=404)

    def _send_json(self, obj: Any, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj, indent=2).encode("utf-8"))
