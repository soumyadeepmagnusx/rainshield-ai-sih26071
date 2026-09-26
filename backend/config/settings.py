"""
Centralized Backend Configuration for RAINSHIELD-AI v6.0 (SIH26071)
Includes Database paths, Provisioned Demo SMTP Credentials, Background Email Scheduler settings,
and ML Training Pipeline artifact paths.
"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
ML_DIR = os.path.join(PROJECT_ROOT, "ml_pipeline")


class AppConfig:
    # Server Configuration
    APP_NAME = "RAINSHIELD-AI v6.0 Command Center Backend"
    PROBLEM_STATEMENT_ID = "SIH26071"
    MINISTRY = "Ministry of Earth Sciences (MoES), Government of India"
    TEAM_NAME = "BWU INCURSION 1.0"
    PORT = int(os.environ.get("PORT", 8090))

    # Relational Database Configuration (SQLite3)
    DB_DIR = os.path.join(BACKEND_DIR, "database")
    DB_PATH = os.path.join(DB_DIR, "rainshield_moes.db")
    SCHEMA_SQL_PATH = os.path.join(DB_DIR, "schema.sql")

    # Provisioned Live Demo SMTP Email Account & Scheduler Configuration
    # (Provisioned via Ethereal SMTP Relay - supports real TLS Port 587 delivery + Webmail inspection)
    SMTP_ENABLED = True
    SMTP_HOST = os.environ.get("RAINSHIELD_SMTP_HOST", "smtp.ethereal.email")
    SMTP_PORT = int(os.environ.get("RAINSHIELD_SMTP_PORT", "587"))
    SMTP_USE_TLS = True
    SMTP_USER = os.environ.get("RAINSHIELD_SMTP_USER", "dzlu6unt5ipokw65@ethereal.email")
    SMTP_PASS = os.environ.get("RAINSHIELD_SMTP_PASS", "uSBGedRn3X2zVarf8p")
    SMTP_SENDER_ADDRESS = os.environ.get(
        "RAINSHIELD_SMTP_FROM",
        "RAINSHIELD-AI MoES Command <dzlu6unt5ipokw65@ethereal.email>"
    )
    DEMO_RECIPIENT_EMAIL = os.environ.get(
        "RAINSHIELD_DEMO_EMAIL",
        "dzlu6unt5ipokw65@ethereal.email"
    )
    DEMO_WEBMAIL_LOGIN_URL = "https://ethereal.email/login"
    DEMO_WEBMAIL_MESSAGES_URL = "https://ethereal.email/messages"

    # Background Email Scheduler Settings
    SCHEDULER_ENABLED = True
    SCHEDULER_INTERVAL_SEC = int(os.environ.get("RAINSHIELD_SCHEDULER_SEC", "300"))
    EMAIL_ARCHIVE_DIR = os.path.join(BACKEND_DIR, "logs", "emails")

    # Machine Learning Dataset & Artifact Paths
    TRAIN_DATASET_CSV = os.path.join(ML_DIR, "datasets", "imd_moes_multimodal_flood_training_2018_2025.csv")
    VAL_DATASET_CSV = os.path.join(ML_DIR, "datasets", "historical_flood_validation_benchmarks.csv")
    DATASET_METADATA_JSON = os.path.join(ML_DIR, "datasets", "dataset_schema_metadata.json")
    TRAINED_MODEL_JSON = os.path.join(ML_DIR, "artifacts", "rainshield_trained_model.json")
    EVAL_METRICS_JSON = os.path.join(ML_DIR, "artifacts", "evaluation_metrics_report.json")
    SHAP_IMPORTANCES_JSON = os.path.join(ML_DIR, "artifacts", "shap_feature_importances.json")

    # Initial Seed Files
    MOCK_GRIDS_JSON = os.path.join(PROJECT_ROOT, "mock_data", "grids.json")
    MOCK_BACKTESTS_JSON = os.path.join(PROJECT_ROOT, "mock_data", "backtests.json")
