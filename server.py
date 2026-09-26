#!/usr/bin/env python3
"""
RAINSHIELD-AI v6.0 Enterprise Backend Server Entrypoint (SIH26071)
Ministry of Earth Sciences (MoES) | Disaster Management | Team BWU INCURSION 1.0

Multi-Tier Architecture:
- `backend/config/`       -> Centralized settings, DB paths, Demo SMTP credentials & Scheduler config
- `backend/database/`     -> SQLite3 Relational Database (`rainshield_moes.db` with 7 normalized tables)
- `backend/services/`     -> TLS SMTP Email Dispatcher + Background Scheduler, SCS-CN Physics & ML Inference
- `backend/controllers/`  -> GridController, AlertController, MLController
- `backend/routes/`       -> Modular REST API Router
- `ml_pipeline/`          -> 2,400-row Training CSV, 400-row Validation CSV, Hybrid GBDT+Ridge Model & Artifacts
"""
import socketserver

from backend.config.settings import AppConfig
from backend.database.db_manager import db_instance
from backend.routes.api_router import RainshieldRequestHandler
from backend.services.ml_inference_service import ml_service
from backend.services.smtp_scheduler_service import smtp_scheduler


def main() -> None:
    # 1. Start the Automated SMTP Alert Email Scheduler Daemon
    smtp_scheduler.start_background_scheduler()
    db_overview = db_instance.get_database_overview()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", AppConfig.PORT), RainshieldRequestHandler) as httpd:
        print("=" * 78)
        print(f"  {AppConfig.APP_NAME} ({AppConfig.PROBLEM_STATEMENT_ID})")
        print(f"  Organization : {AppConfig.MINISTRY} | Team: {AppConfig.TEAM_NAME}")
        print(f"  Server URL   : http://localhost:{AppConfig.PORT}")
        print(f"  SQLite DB    : {db_overview['db_file_path']} ({len(db_overview['table_row_counts'])} Tables Active)")
        print(f"  Demo Email   : {AppConfig.DEMO_RECIPIENT_EMAIL} (SMTP: {AppConfig.SMTP_HOST}:{AppConfig.SMTP_PORT} TLS)")
        print(f"  ML Pipeline  : Model Loaded={ml_service.model.is_trained} | Training CSV=2,400 rows | Holdout=400 rows")
        print("=" * 78)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
