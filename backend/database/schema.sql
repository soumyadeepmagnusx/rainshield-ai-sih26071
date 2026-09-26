-- ============================================================================
-- RAINSHIELD-AI v6.0 Relational Database Schema (SQLite3 / PostgreSQL Compatible)
-- Problem Statement: SIH26071 (Ministry of Earth Sciences - Government of India)
-- ============================================================================

CREATE TABLE IF NOT EXISTS flood_basins (
    grid_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    river_basin TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    alert_level TEXT NOT NULL,
    confidence_pct REAL NOT NULL,
    fused_rain_mm_hr REAL NOT NULL,
    inundation_depth_m REAL NOT NULL,
    uncertainty_m REAL NOT NULL,
    population_exposed INTEGER NOT NULL,
    full_payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sensor_telemetry_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grid_id TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    insat_bt_k REAL NOT NULL,
    gsmap_rain_mm_hr REAL NOT NULL,
    dwr_reflectivity_dbz REAL NOT NULL,
    aws_rain_mm_hr REAL NOT NULL,
    nwp_rain_mm_hr REAL NOT NULL,
    fused_rain_mm_hr REAL NOT NULL,
    predicted_depth_m REAL NOT NULL,
    FOREIGN KEY (grid_id) REFERENCES flood_basins(grid_id)
);

CREATE TABLE IF NOT EXISTS alert_transmissions (
    transmission_id TEXT PRIMARY KEY,
    grid_id TEXT NOT NULL,
    channel TEXT NOT NULL,          -- e.g. 'CELL_BROADCAST_SMS', 'CAP_VOICE_IVR', 'EVAC_ROUTE_DEPLOY', 'SCHEDULED_DIGEST'
    severity TEXT NOT NULL,         -- 'RED', 'ORANGE', 'YELLOW', 'GREEN'
    language TEXT NOT NULL,         -- 'en-IN', 'hi-IN', 'as-IN', 'ta-IN', 'mr-IN', 'bn-IN'
    message_summary TEXT NOT NULL,
    population_targeted INTEGER NOT NULL,
    triggered_by TEXT NOT NULL,
    email_dispatch_id TEXT,
    transmitted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_dispatch_logs (
    dispatch_id TEXT PRIMARY KEY,
    transmission_id TEXT NOT NULL,
    grid_id TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    sender_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    smtp_host TEXT NOT NULL,
    smtp_port INTEGER NOT NULL,
    delivery_status TEXT NOT NULL,  -- 'SENT_TLS_250_OK', 'QUEUED_FALLBACK', 'SCHEDULED_SENT'
    smtp_response TEXT NOT NULL,
    webmail_inbox_url TEXT NOT NULL,
    archived_html_path TEXT NOT NULL,
    dispatched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_jobs (
    job_id TEXT PRIMARY KEY,
    job_name TEXT NOT NULL,
    schedule_interval_sec INTEGER NOT NULL,
    target_demo_email TEXT NOT NULL,
    smtp_host TEXT NOT NULL,
    status TEXT NOT NULL,
    total_runs INTEGER NOT NULL DEFAULT 0,
    last_run_at TEXT,
    next_run_at TEXT
);

CREATE TABLE IF NOT EXISTS hitl_audit_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL,
    role TEXT NOT NULL,
    grid_id TEXT NOT NULL,
    action TEXT NOT NULL,
    hash TEXT NOT NULL,
    details TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ml_training_runs (
    run_id TEXT PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    model_architecture TEXT NOT NULL,
    training_rows INTEGER NOT NULL,
    validation_rows INTEGER NOT NULL,
    rainfall_rmse REAL NOT NULL,
    inundation_rmse REAL NOT NULL,
    inundation_r2 REAL NOT NULL,
    pod_score REAL NOT NULL,
    far_score REAL NOT NULL,
    csi_score REAL NOT NULL,
    brier_score REAL NOT NULL,
    duration_ms REAL NOT NULL,
    artifact_path TEXT NOT NULL
);
