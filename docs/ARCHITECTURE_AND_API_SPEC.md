# 🏛️ RAINSHIELD-AI v6.0: System Architecture, Database ER Diagram & REST API Specification
**Problem Statement ID:** `SIH26071` | **Ministry of Earth Sciences (MoES)** | **Team:** `BWU INCURSION 1.0`

---

## 1. End-to-End Multi-Modal System Architecture

```mermaid
flowchart LR
    subgraph DATA["1. Multi-Source MoES Telemetry"]
        S1["INSAT-3DS TIR-1 + GSMaP-ISRO"]
        S2["IMD S-Band Doppler Radar (dBZ)"]
        S3["IMD AWS/ARG Ground Gauges"]
        S4["NCMRWF 1km Downscaled NWP"]
    end

    subgraph ML["2. Physics-Informed ML Pipeline"]
        FE["18D Feature Engineering (Marshall-Palmer + SCS-CN)"]
        MOD["Hybrid Ridge + 20-Stage GBDT Ensemble (Trained on 2,400 Rows)"]
        SHAP["SHAP Attribution & Confidence Calibration"]
    end

    subgraph BACKEND["3. Multi-Tier Enterprise Backend"]
        API["Modular REST Router (backend/routes)"]
        DB[("SQLite3 Relational DB (7 Tables)")]
        SMTP["TLS Port 587 SMTP Scheduler (JOB-MOES-SMTP-01)"]
    end

    subgraph ALERT["4. Command Center & Last-Mile Dissemination"]
        UI["Cyber-Command Center GIS & 24h Scrubber"]
        CAP["ITU-T X.1303 / NDMA CAP v1.2 XML"]
        VOICE["6-Language Voice Alert + Demo Email Inbox"]
    end

    S1 & S2 & S3 & S4 --> FE --> MOD --> SHAP --> API
    API <--> DB
    API --> SMTP --> VOICE
    API --> UI & CAP
```

---

## 2. Relational Database Entity-Relationship Schema (`rainshield_moes.db`)

```mermaid
erDiagram
    FLOOD_BASINS ||--o{ SENSOR_TELEMETRY_HISTORY : records
    FLOOD_BASINS ||--o{ ALERT_TRANSMISSIONS : triggers
    ALERT_TRANSMISSIONS ||--|| EMAIL_DISPATCH_LOGS : dispatches
    FLOOD_BASINS ||--o{ HITL_AUDIT_LEDGER : audits

    FLOOD_BASINS {
        text grid_id PK
        text name
        text state
        text alert_level
        real fused_rain_mm_hr
        real inundation_depth_m
        integer population_exposed
    }
    ALERT_TRANSMISSIONS {
        text transmission_id PK
        text grid_id FK
        text channel
        text severity
        text language
        text email_dispatch_id FK
        text transmitted_at
    }
    EMAIL_DISPATCH_LOGS {
        text dispatch_id PK
        text transmission_id FK
        text recipient_email
        text delivery_status
        text smtp_response
        text dispatched_at
    }
    SCHEDULER_JOBS {
        text job_id PK
        integer schedule_interval_sec
        text target_demo_email
        integer total_runs
    }
    ML_TRAINING_RUNS {
        text run_id PK
        integer training_rows
        integer validation_rows
        real inundation_r2
        real pod_score
        real csi_score
    }
```

---

## 3. REST API Specification (`backend/routes/api_router.py`)

| Method | Endpoint | Controller | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/grids` | `GridController` | Returns all 6 `1km × 1km` flood basins from SQLite `flood_basins` |
| `GET` | `/api/backtests` | `GridController` | Returns 4 historical flood benchmark datasets (Michaung, Mumbai, Guwahati, Wayanad) |
| `GET` | `/api/simulate` | `GridController` | Computes real-time USDA/NRSC `SCS-CN` runoff $Q$ and 2D inundation depth |
| `POST` | `/api/alerts/transmit` | `AlertController` | Records alert transmission in SQLite and sends live `STARTTLS` email via `smtp.ethereal.email:587` |
| `GET` | `/api/alerts/emails` | `AlertController` | Returns provisioned Demo SMTP credentials, scheduler status, and recent email dispatch logs |
| `GET` | `/api/ml/overview` | `MLController` | Returns 2,400-row dataset preview, trained model metrics ($R^2, \text{POD}, \text{FAR}, \text{CSI}$), and DB counts |
| `POST` | `/api/ml/retrain` | `MLController` | Retrains the Hybrid Ridge + GBDT model on the 2,400-row training CSV and logs to SQLite |
| `POST` | `/api/scada` | `GridController` | Updates municipal SCADA pump RPM, sluice gate opening, and tidal backwater lock |
| `POST` | `/api/override` | `AlertController` | Logs SHA-256 Human-in-the-Loop authority override and dispatches SMTP confirmation |
| `GET` | `/api/cap/<grid_id>` | `AlertController` | Generates downloadable ITU-T X.1303 / NDMA SACHET `CAP v1.2` XML packet |
