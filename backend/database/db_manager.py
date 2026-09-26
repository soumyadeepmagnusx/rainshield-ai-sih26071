"""
SQLite3 Relational Database Manager for RAINSHIELD-AI v6.0 (SIH26071)
Manages 7 normalized tables:
- flood_basins
- sensor_telemetry_history
- alert_transmissions
- email_dispatch_logs
- scheduler_jobs
- hitl_audit_ledger
- ml_training_runs
"""
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from backend.config.settings import AppConfig

IST = timezone(timedelta(hours=5, minutes=30))


class DatabaseManager:
    def __init__(self, db_path: str = AppConfig.DB_PATH) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialize_schema()
        self._seed_initial_data()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                with open(AppConfig.SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
            finally:
                conn.close()

    def _seed_initial_data(self) -> None:
        now_ist = datetime.now(IST).isoformat()
        with self._lock:
            conn = self._get_conn()
            try:
                # 1. Seed flood_basins from mock_data/grids.json if empty
                cur = conn.execute("SELECT COUNT(*) as cnt FROM flood_basins")
                if cur.fetchone()["cnt"] == 0 and os.path.exists(AppConfig.MOCK_GRIDS_JSON):
                    with open(AppConfig.MOCK_GRIDS_JSON, "r", encoding="utf-8") as f:
                        grids_raw = json.load(f)
                    grids_list = grids_raw if isinstance(grids_raw, list) else grids_raw.get("grids", [])
                    for g in grids_list:
                        gid = g.get("id") or g.get("grid_id")
                        s = g.get("sources", {})
                        conn.execute(
                            """
                            INSERT INTO flood_basins (
                                grid_id, name, state, river_basin, lat, lon,
                                alert_level, confidence_pct, fused_rain_mm_hr,
                                inundation_depth_m, uncertainty_m, population_exposed,
                                full_payload_json, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                gid,
                                g.get("name", gid),
                                g.get("state", "India"),
                                g.get("district", "Urban Flood Basin"),
                                float(g.get("lat", 19.07)),
                                float(g.get("lng", g.get("lon", 72.88))),
                                g.get("alert_color", g.get("alert_level", "RED")),
                                float(g.get("confidence_score_pct", 94.0)),
                                float(g.get("fused_rainfall_mm_hr", 95.0)),
                                float(g.get("predicted_inundation_depth_m", 1.5)),
                                float(g.get("ensemble_uncertainty_m", 0.18)),
                                int(g.get("affected_population", 100000)),
                                json.dumps(g),
                                now_ist
                            )
                        )
                        conn.execute(
                            """
                            INSERT INTO sensor_telemetry_history (
                                grid_id, recorded_at, insat_bt_k, gsmap_rain_mm_hr,
                                dwr_reflectivity_dbz, aws_rain_mm_hr, nwp_rain_mm_hr,
                                fused_rain_mm_hr, predicted_depth_m
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                gid,
                                now_ist,
                                float(s.get("insat_3ds_tir_k", 195.0)),
                                float(s.get("gsmap_isro_mm_hr", 92.0)),
                                float(s.get("imd_dwr_dbz", 62.0)),
                                float(s.get("aws_gauge_mm_hr", 98.0)),
                                float(s.get("nwp_downscaled_1km_mm_hr", 90.0)),
                                float(g.get("fused_rainfall_mm_hr", 95.0)),
                                float(g.get("predicted_inundation_depth_m", 1.5))
                            )
                        )

                # 2. Seed scheduler_jobs if empty
                cur = conn.execute("SELECT COUNT(*) as cnt FROM scheduler_jobs")
                if cur.fetchone()["cnt"] == 0:
                    next_run = (datetime.now(IST) + timedelta(seconds=AppConfig.SCHEDULER_INTERVAL_SEC)).isoformat()
                    conn.execute(
                        """
                        INSERT INTO scheduler_jobs (
                            job_id, job_name, schedule_interval_sec,
                            target_demo_email, smtp_host, status,
                            total_runs, last_run_at, next_run_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "JOB-MOES-SMTP-01",
                            "SIH26071 Automated Critical Flood Alert & CAP Email Dispatcher",
                            AppConfig.SCHEDULER_INTERVAL_SEC,
                            AppConfig.DEMO_RECIPIENT_EMAIL,
                            f"{AppConfig.SMTP_HOST}:{AppConfig.SMTP_PORT}",
                            "ACTIVE_RUNNING",
                            0,
                            now_ist,
                            next_run
                        )
                    )

                # 3. Seed hitl_audit_ledger if empty
                cur = conn.execute("SELECT COUNT(*) as cnt FROM hitl_audit_ledger")
                if cur.fetchone()["cnt"] == 0:
                    initial_logs = [
                        (
                            now_ist,
                            "RAINSHIELD-Ensemble-v6.0",
                            "AI Autonomous Pipeline",
                            "GRID-MUM-01",
                            "AUTO_ESCALATE_RED",
                            "SHA256:9f8e2a11c40b",
                            "4-source fusion (107.0 mm/hr) + SCS-CN runoff (90.5 mm/hr) exceeded 1.15m inundation threshold (Confidence: 94.2%)."
                        ),
                        (
                            now_ist,
                            "Dr. R. K. Baruah (ASDMA)",
                            "State Disaster Duty Officer",
                            "GRID-GUW-02",
                            "HITL_CONFIRMED_RED",
                            "SHA256:4b12d908e77a",
                            "Confirmed Meghalaya foothills runoff via AWS-DISPUR-01; authorized CAP XML + Assamese IVR & SMTP dispatch."
                        )
                    ]
                    conn.executemany(
                        """
                        INSERT INTO hitl_audit_ledger (timestamp, actor, role, grid_id, action, hash, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        initial_logs
                    )

                # 4. Seed ml_training_runs from evaluation_metrics_report.json if empty
                cur = conn.execute("SELECT COUNT(*) as cnt FROM ml_training_runs")
                if cur.fetchone()["cnt"] == 0 and os.path.exists(AppConfig.EVAL_METRICS_JSON):
                    with open(AppConfig.EVAL_METRICS_JSON, "r", encoding="utf-8") as f:
                        rep = json.load(f)
                    vm = rep["validation_metrics"]
                    conn.execute(
                        """
                        INSERT INTO ml_training_runs (
                            run_id, timestamp_utc, model_architecture,
                            training_rows, validation_rows, rainfall_rmse,
                            inundation_rmse, inundation_r2, pod_score,
                            far_score, csi_score, brier_score,
                            duration_ms, artifact_path
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rep["run_id"],
                            rep["timestamp_utc"],
                            rep["model_architecture"],
                            int(rep["training_dataset"]["records"]),
                            int(rep["validation_dataset"]["records"]),
                            float(vm["rainfall_rmse_mm_hr"]),
                            float(vm["inundation_depth_rmse_m"]),
                            float(vm["inundation_r2_score"]),
                            float(vm["probability_of_detection_pod"]),
                            float(vm["false_alarm_ratio_far"]),
                            float(vm["critical_success_index_csi"]),
                            float(vm["brier_skill_score"]),
                            float(rep["training_duration_ms"]),
                            "ml_pipeline/artifacts/rainshield_trained_model.json"
                        )
                    )

                conn.commit()
            finally:
                conn.close()

    def get_all_grids(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute("SELECT full_payload_json FROM flood_basins ORDER BY grid_id").fetchall()
                return [json.loads(r["full_payload_json"]) for r in rows]
            finally:
                conn.close()

    def get_grid_by_id(self, grid_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT full_payload_json FROM flood_basins WHERE grid_id = ?",
                    (grid_id,)
                ).fetchone()
                return json.loads(row["full_payload_json"]) if row else None
            finally:
                conn.close()

    def update_grid_payload(self, grid_id: str, payload: Dict[str, Any]) -> None:
        now_ist = datetime.now(IST).isoformat()
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    UPDATE flood_basins
                    SET alert_level = ?,
                        confidence_pct = ?,
                        fused_rain_mm_hr = ?,
                        inundation_depth_m = ?,
                        full_payload_json = ?,
                        updated_at = ?
                    WHERE grid_id = ?
                    """,
                    (
                        payload.get("alert_color", payload.get("alert_level", "RED")),
                        float(payload.get("confidence_score_pct", 94.0)),
                        float(payload.get("fused_rainfall_mm_hr", 107.0)),
                        float(payload.get("predicted_inundation_depth_m", 1.85)),
                        json.dumps(payload),
                        now_ist,
                        grid_id
                    )
                )
                conn.commit()
            finally:
                conn.close()

    def record_alert_transmission(
        self,
        transmission_id: str,
        grid_id: str,
        channel: str,
        severity: str,
        language: str,
        message_summary: str,
        population_targeted: int,
        triggered_by: str,
        email_dispatch_id: str
    ) -> Dict[str, Any]:
        now_ist = datetime.now(IST).isoformat()
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO alert_transmissions (
                        transmission_id, grid_id, channel, severity, language,
                        message_summary, population_targeted, triggered_by,
                        email_dispatch_id, transmitted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transmission_id,
                        grid_id,
                        channel,
                        severity,
                        language,
                        message_summary,
                        population_targeted,
                        triggered_by,
                        email_dispatch_id,
                        now_ist
                    )
                )
                conn.commit()
            finally:
                conn.close()
        return {
            "transmission_id": transmission_id,
            "grid_id": grid_id,
            "channel": channel,
            "severity": severity,
            "language": language,
            "message_summary": message_summary,
            "population_targeted": population_targeted,
            "triggered_by": triggered_by,
            "email_dispatch_id": email_dispatch_id,
            "transmitted_at": now_ist
        }

    def record_email_dispatch(
        self,
        dispatch_id: str,
        transmission_id: str,
        grid_id: str,
        recipient_email: str,
        sender_email: str,
        subject: str,
        smtp_host: str,
        smtp_port: int,
        delivery_status: str,
        smtp_response: str,
        webmail_inbox_url: str,
        archived_html_path: str
    ) -> Dict[str, Any]:
        now_ist = datetime.now(IST).isoformat()
        next_run = (datetime.now(IST) + timedelta(seconds=AppConfig.SCHEDULER_INTERVAL_SEC)).isoformat()
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO email_dispatch_logs (
                        dispatch_id, transmission_id, grid_id, recipient_email,
                        sender_email, subject, smtp_host, smtp_port,
                        delivery_status, smtp_response, webmail_inbox_url,
                        archived_html_path, dispatched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dispatch_id,
                        transmission_id,
                        grid_id,
                        recipient_email,
                        sender_email,
                        subject,
                        smtp_host,
                        smtp_port,
                        delivery_status,
                        smtp_response,
                        webmail_inbox_url,
                        archived_html_path,
                        now_ist
                    )
                )
                conn.execute(
                    """
                    UPDATE scheduler_jobs
                    SET total_runs = total_runs + 1,
                        last_run_at = ?,
                        next_run_at = ?
                    WHERE job_id = 'JOB-MOES-SMTP-01'
                    """,
                    (now_ist, next_run)
                )
                conn.commit()
            finally:
                conn.close()
        return {
            "dispatch_id": dispatch_id,
            "transmission_id": transmission_id,
            "grid_id": grid_id,
            "recipient_email": recipient_email,
            "sender_email": sender_email,
            "subject": subject,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "delivery_status": delivery_status,
            "smtp_response": smtp_response,
            "webmail_inbox_url": webmail_inbox_url,
            "archived_html_path": archived_html_path,
            "dispatched_at": now_ist
        }

    def get_recent_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT * FROM email_dispatch_logs ORDER BY dispatched_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def get_recent_transmissions(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT * FROM alert_transmissions ORDER BY transmitted_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def get_scheduler_status(self) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT * FROM scheduler_jobs WHERE job_id = 'JOB-MOES-SMTP-01'").fetchone()
                return dict(row) if row else {}
            finally:
                conn.close()

    def insert_audit_log(self, entry: Dict[str, str]) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO hitl_audit_ledger (timestamp, actor, role, grid_id, action, hash, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry["timestamp"],
                        entry["actor"],
                        entry["role"],
                        entry["grid_id"],
                        entry["action"],
                        entry["hash"],
                        entry["details"]
                    )
                )
                conn.commit()
            finally:
                conn.close()

    def get_audit_logs(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT timestamp, actor, role, grid_id, action, hash, details FROM hitl_audit_ledger ORDER BY id DESC LIMIT ?",
                    (limit,)
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def record_ml_training_run(self, report: Dict[str, Any]) -> None:
        vm = report["validation_metrics"]
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO ml_training_runs (
                        run_id, timestamp_utc, model_architecture,
                        training_rows, validation_rows, rainfall_rmse,
                        inundation_rmse, inundation_r2, pod_score,
                        far_score, csi_score, brier_score,
                        duration_ms, artifact_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report["run_id"],
                        report["timestamp_utc"],
                        report["model_architecture"],
                        int(report["training_dataset"]["records"]),
                        int(report["validation_dataset"]["records"]),
                        float(vm["rainfall_rmse_mm_hr"]),
                        float(vm["inundation_depth_rmse_m"]),
                        float(vm["inundation_r2_score"]),
                        float(vm["probability_of_detection_pod"]),
                        float(vm["false_alarm_ratio_far"]),
                        float(vm["critical_success_index_csi"]),
                        float(vm["brier_skill_score"]),
                        float(report["training_duration_ms"]),
                        "ml_pipeline/artifacts/rainshield_trained_model.json"
                    )
                )
                conn.commit()
            finally:
                conn.close()

    def get_database_overview(self) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            try:
                tables = [
                    "flood_basins",
                    "sensor_telemetry_history",
                    "alert_transmissions",
                    "email_dispatch_logs",
                    "scheduler_jobs",
                    "hitl_audit_ledger",
                    "ml_training_runs"
                ]
                counts = {}
                for t in tables:
                    c = conn.execute(f"SELECT COUNT(*) as cnt FROM {t}").fetchone()["cnt"]
                    counts[t] = c
                ml_runs = [
                    dict(r) for r in conn.execute("SELECT * FROM ml_training_runs ORDER BY timestamp_utc DESC LIMIT 5").fetchall()
                ]
                return {
                    "db_engine": "SQLite 3 Relational Engine (ACID WAL-Ready)",
                    "db_file_path": "backend/database/rainshield_moes.db",
                    "db_size_bytes": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                    "table_row_counts": counts,
                    "recent_ml_runs": ml_runs
                }
            finally:
                conn.close()


db_instance = DatabaseManager()
