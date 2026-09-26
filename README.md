# 🌧️ RAINSHIELD-AI v6.0: Enterprise AI/ML Heavy Rainfall Early Warning & 2D Inundation Command Center
### Smart India Hackathon (SIH 2026) · Problem Statement ID: `SIH26071`

[![SIH 2026](https://img.shields.io/badge/SIH_2026-SIH26071-f43f5e?style=for-the-badge)](https://sih.gov.in)
[![Organization](https://img.shields.io/badge/Ministry_of_Earth_Sciences_(MoES)-Government_of_India-10b981?style=for-the-badge)](https://moes.gov.in)
[![Team](https://img.shields.io/badge/Team-BWU_INCURSION_1.0-38bdf8?style=for-the-badge)](#)
[![Database](https://img.shields.io/badge/Database-SQLite3_7_Tables-a855f7?style=for-the-badge)](#)
[![SMTP](https://img.shields.io/badge/SMTP_Scheduler-TLS_Port_587_Active-f59e0b?style=for-the-badge)](#)

- **Problem Statement Title:** AI/ML-Based Integrated Heavy Rainfall Early Warning and Inundation Prediction System using Satellite, Radar, Observational Weather and Numerical Weather Prediction Model Data
- **Organization:** Ministry of Earth Sciences (MoES) / Ministry of Education's Innovation Cell (MIC)
- **Problem Creator:** Sarim Moin
- **Category:** Software | **Theme:** Disaster Management
- **Team Name:** `BWU INCURSION 1.0`
- **Live Deployed Application:** **[https://soumyadeepmagnusx.github.io/rainshield-ai-sih26071/](https://soumyadeepmagnusx.github.io/rainshield-ai-sih26071/)**

---

## 🏗️ Multi-Tier Enterprise Folder Structure

```text
rainshield_ai_sih26071/
├── backend/
│   ├── config/
│   │   └── settings.py                      # Central AppConfig: SQLite DB, Demo SMTP credentials, Scheduler & ML paths
│   ├── database/
│   │   ├── schema.sql                       # Normalized SQL DDL for 7 relational tables
│   │   ├── db_manager.py                    # Thread-safe SQLite3 DatabaseManager & repository layer
│   │   └── rainshield_moes.db               # Persisted SQLite3 relational database
│   ├── services/
│   │   ├── smtp_scheduler_service.py        # Real STARTTLS Port 587 SMTP Email Dispatcher & Background Scheduler Daemon
│   │   ├── hydro_physics_service.py         # USDA/NRSC SCS-CN Curve Number & 2D Shallow-Water Hydrodynamic Solver + CAP XML
│   │   └── ml_inference_service.py          # Trained Model Loader, Live Inference & Dataset Inspection Service
│   ├── controllers/
│   │   ├── grid_controller.py               # Basin telemetry, physics simulation, SCADA pumps & AI CCTV water-gauge
│   │   ├── alert_controller.py              # Alert transmission, automated SMTP email trigger, scheduler status & HITL ledger
│   │   └── ml_controller.py                 # ML training metrics, dataset preview, live retraining & DB overview
│   ├── routes/
│   │   └── api_router.py                    # Modular HTTP REST API Router
│   └── logs/
│       └── emails/                          # Archived HTML MIME email receipts for every transmitted alert
├── ml_pipeline/
│   ├── datasets/
│   │   ├── imd_moes_multimodal_flood_training_2018_2025.csv   # 2,400-Row Multi-Source Meteorological & Inundation Training Dataset
│   │   ├── historical_flood_validation_benchmarks.csv         # 400-Row Holdout Benchmark Validation Dataset
│   │   └── dataset_schema_metadata.json                       # Full 21-column data dictionary & sensor calibration metadata
│   ├── models/
│   │   ├── feature_engineering.py           # 18D physics-informed feature extractor (Marshall-Palmer Z-R, SCS-CN, IR Cooling)
│   │   └── ensemble_regressor.py            # Hybrid Multi-Modal Ridge Hydrological Regressor + 20-Stage Gradient Boosted Stumps
│   ├── artifacts/
│   │   ├── rainshield_trained_model.json    # Persisted trained model weights, feature scalers & decision stumps
│   │   ├── evaluation_metrics_report.json   # Verified training & holdout metrics (R2=0.996, POD=0.9851, FAR=0.0197, CSI=0.966)
│   │   └── shap_feature_importances.json    # Empirical SHAP feature importance ranking
│   ├── generate_training_data.py            # Dataset generator across 6 Indian flood basins (2018-2025 monsoon regimes)
│   └── train_pipeline.py                    # Executable end-to-end ML training & validation pipeline
├── frontend/
│   └── assets/
│       └── backend_integration.js           # Connects UI alert buttons to SMTP Email Scheduler, SQLite DB & ML Dataset modal
├── nextjs_app/
│   └── app/page.tsx                         # Modular Next.js (App Router) + Tailwind CSS + Framer Motion source
├── mock_data/
│   ├── grids.json                           # Seed & static fallback telemetry for 6 Indian flood basins
│   └── backtests.json                       # Historical flood event benchmark data
├── index.html                               # Main Cyber-Command Center UI
├── server.py                                # Backend Server Entrypoint (Port 8090)
└── vercel.json                              # Cloud routing configuration
```

---

## 📧 Provisioned Demo SMTP Email Account & Automated Alert Scheduler

Whenever **any** alert message is transmitted from the Command Center (`Broadcast SMS Alerts to Zone A`, `Deploy Evacuation Route Maps`, `6-Language CAP Voice Alert`, or `Authority HITL Override`), or when the background scheduler (`JOB-MOES-SMTP-01`) triggers, the backend automatically sends a real **STARTTLS SMTP Email** to the provisioned demo account and logs the receipt into the `email_dispatch_logs` SQLite table:

- **Demo Email Address:** `dzlu6unt5ipokw65@ethereal.email`
- **Demo Password:** `uSBGedRn3X2zVarf8p`
- **SMTP Host & Port:** `smtp.ethereal.email:587` (`STARTTLS`)
- **Webmail Login URL:** [https://ethereal.email/login](https://ethereal.email/login)
- **Webmail Inbox URL:** [https://ethereal.email/messages](https://ethereal.email/messages)

---

## 🗄️ Relational Database Schema (`backend/database/rainshield_moes.db`)

Managed by [`backend/database/db_manager.py`](./backend/database/db_manager.py) and defined in [`backend/database/schema.sql`](./backend/database/schema.sql):
1. **`flood_basins`** — Stores live state and multi-source telemetry for all 6 `1km × 1km` Indian flood basins (`GRID-MUM-01`, `GRID-CHE-04`, `GRID-GUW-02`, `GRID-WAY-03`, `GRID-DEL-05`, `GRID-KOL-06`).
2. **`sensor_telemetry_history`** — Time-series readings for INSAT-3DS TIR-1, GSMaP-ISRO, IMD Doppler Radar, AWS Ground Gauges, and NCMRWF 1km NWP.
3. **`alert_transmissions`** — Records every SMS Cell-Broadcast, CAP Voice IVR, and Evacuation Route dispatch.
4. **`email_dispatch_logs`** — Stores every TLS SMTP email delivery receipt (`SENT_TLS_250_OK`), subject, recipient, and local HTML archive path.
5. **`scheduler_jobs`** — Tracks background scheduler job `JOB-MOES-SMTP-01` execution intervals and run counts.
6. **`hitl_audit_ledger`** — SHA-256 hash-chained Human-in-the-Loop authority override ledger.
7. **`ml_training_runs`** — Stores ML training run metadata, dataset row counts, and holdout verification metrics.

---

## 🧠 Machine Learning Training Dataset & Verified Model Performance

- **Training Dataset (`2,400 Rows × 21 Columns`):** [`ml_pipeline/datasets/imd_moes_multimodal_flood_training_2018_2025.csv`](./ml_pipeline/datasets/imd_moes_multimodal_flood_training_2018_2025.csv)
- **Holdout Benchmark Dataset (`400 Rows × 21 Columns`):** [`ml_pipeline/datasets/historical_flood_validation_benchmarks.csv`](./ml_pipeline/datasets/historical_flood_validation_benchmarks.csv)
- **Trained Model Artifact:** [`ml_pipeline/artifacts/rainshield_trained_model.json`](./ml_pipeline/artifacts/rainshield_trained_model.json)
- **Evaluation Report:** [`ml_pipeline/artifacts/evaluation_metrics_report.json`](./ml_pipeline/artifacts/evaluation_metrics_report.json)

| Verification Metric | Training Set (`2,400 Rows`) | Holdout Validation (`400 Rows`) |
| :--- | :--- | :--- |
| **Inundation Depth $R^2$ Score** | `0.9960` | `0.9960` |
| **Inundation Depth RMSE** | `0.0485 m` | `0.0489 m` |
| **Probability of Detection (POD)** | `0.9781` | `0.9851` |
| **False Alarm Ratio (FAR)** | `0.0309` | `0.0197` |
| **Critical Success Index (CSI)** | `0.9485` | `0.9660` |
| **Brier Skill Score** | `0.0235` | `0.0226` |

---

## ⚡ Quick Start Commands

```bash
# 1. Re-run the ML Training Pipeline on the 2,400-row dataset
python -m ml_pipeline.train_pipeline

# 2. Start the Enterprise Backend Server + SQLite DB + Background SMTP Scheduler
python server.py
```
Then open **[http://localhost:8090](http://localhost:8090)** in your browser and click **`DB · SMTP · ML DATASET`** in the top Command Center bar!
