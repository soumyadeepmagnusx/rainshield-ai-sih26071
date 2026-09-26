"""
Alert Transmission, SMTP Email Dispatch, Scheduler Status & Authority HITL Override Controller
for RAINSHIELD-AI v6.0 (SIH26071 - Ministry of Earth Sciences).
"""
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple

from backend.config.settings import AppConfig
from backend.database.db_manager import db_instance
from backend.services.hydro_physics_service import hydro_service
from backend.services.smtp_scheduler_service import smtp_scheduler

IST = timezone(timedelta(hours=5, minutes=30))


class AlertController:
    def handle_alert_transmission(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triggered whenever an alert message is transmitted (SMS Broadcast, CAP Voice Alert,
        Evacuation Route Deployment, or Manual Test Dispatch).
        Automatically sends a real email via TLS SMTP to the configured Demo Email Account.
        """
        grid_id = body.get("grid_id", "GRID-MUM-01")
        channel = body.get("channel", "CELL_BROADCAST_SMS")
        language = body.get("language", "en-IN")
        custom_message = body.get("message")
        recipient_override = body.get("recipient_email")
        triggered_by = body.get("triggered_by", "MoES Command Center Duty Officer")

        return smtp_scheduler.transmit_alert_and_send_email(
            grid_id=grid_id,
            channel=channel,
            language=language,
            custom_message=custom_message,
            recipient_override=recipient_override,
            triggered_by=triggered_by
        )

    def get_email_and_scheduler_dashboard(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "demo_smtp_account": {
                "email": AppConfig.SMTP_USER,
                "password": AppConfig.SMTP_PASS,
                "smtp_host": AppConfig.SMTP_HOST,
                "smtp_port": AppConfig.SMTP_PORT,
                "tls_enabled": AppConfig.SMTP_USE_TLS,
                "webmail_login_url": AppConfig.DEMO_WEBMAIL_LOGIN_URL,
                "webmail_messages_url": AppConfig.DEMO_WEBMAIL_MESSAGES_URL
            },
            "scheduler_job": db_instance.get_scheduler_status(),
            "recent_emails": db_instance.get_recent_emails(limit=20),
            "recent_transmissions": db_instance.get_recent_transmissions(limit=20)
        }

    def handle_hitl_override(self, body: Dict[str, Any]) -> Dict[str, Any]:
        grid_id = body.get("grid_id", "GRID-MUM-01")
        new_level = body.get("new_alert_level", "RED")
        officer = body.get("officer_name", "Duty Officer (IMD/NDMA)")
        role = body.get("role", "Incident Commander")
        reason = body.get("reason", "Manual verification via DWR + AWS telemetry.")

        grid = db_instance.get_grid_by_id(grid_id)
        if grid:
            grid["alert_level"] = new_level
            db_instance.update_grid_payload(grid_id, grid)

        now_ist = datetime.now(IST).isoformat()
        raw_hash = hashlib.sha256(f"{now_ist}|{officer}|{grid_id}|{new_level}|{reason}".encode()).hexdigest()[:12]
        entry = {
            "timestamp": now_ist,
            "actor": officer,
            "role": role,
            "grid_id": grid_id,
            "action": f"HITL_OVERRIDE_{new_level}",
            "hash": f"SHA256:{raw_hash}",
            "details": reason
        }
        db_instance.insert_audit_log(entry)

        # Also dispatch an automated SMTP alert email for the authority override
        email_res = smtp_scheduler.transmit_alert_and_send_email(
            grid_id=grid_id,
            channel=f"HITL_AUTHORITY_OVERRIDE_{new_level}",
            language="en-IN",
            custom_message=f"Authority Override by {officer} ({role}): Escalated/Set {grid_id} to {new_level}. Rationale: {reason}",
            triggered_by=f"{officer} ({role})"
        )

        return {
            "status": "ok",
            "entry": entry,
            "email_dispatch": email_res["email_dispatch"],
            "audit_logs": db_instance.get_audit_logs(limit=15)
        }

    def get_audit_logs_response(self) -> Dict[str, Any]:
        return {"audit_logs": db_instance.get_audit_logs(limit=25)}

    def get_cap_xml_response(self, grid_id: str) -> Tuple[str, str]:
        grid = db_instance.get_grid_by_id(grid_id) or db_instance.get_all_grids()[0]
        xml_str = hydro_service.generate_cap_xml(grid)
        return xml_str, grid["grid_id"]


alert_controller = AlertController()
