"""
Machine Learning Dataset, Training Metrics, Live Retraining & Database Overview Controller
for RAINSHIELD-AI v6.0 (SIH26071 - Ministry of Earth Sciences).
"""
from typing import Any, Dict

from backend.database.db_manager import db_instance
from backend.services.imd_mosaic_ingestor import imd_ingestor
from backend.services.ml_inference_service import ml_service
from ml_pipeline.models.convlstm_gnn_pinn import compute_shallow_water_pinn_residual


class MLController:
    def get_ml_and_db_dashboard(self) -> Dict[str, Any]:
        ml_info = ml_service.get_training_report_and_dataset_preview(sample_limit=12)
        db_info = db_instance.get_database_overview()
        pinn_check = compute_shallow_water_pinn_residual(
            h_prev_m=1.42,
            h_pred_m=1.85,
            dt_hr=1.0,
            fused_rain_mm_hr=107.0,
            scs_infiltration_mm_hr=16.5,
            scada_drainage_mm_hr=42.0
        )
        return {
            "status": "ok",
            "database_overview": db_info,
            "ml_pipeline": ml_info,
            "pinn_pde_verification": pinn_check
        }

    def trigger_retrain(self) -> Dict[str, Any]:
        res = ml_service.trigger_live_retrain()
        res["database_overview"] = db_instance.get_database_overview()
        return res

    def predict_custom(self, body: Dict[str, Any]) -> Dict[str, Any]:
        pred = ml_service.predict_from_features(body)
        return {"status": "ok", "prediction": pred}

    def handle_live_synoptic_scan(self, lat: float, lon: float, scs_cn: float = 91.0) -> Dict[str, Any]:
        return imd_ingestor.fetch_live_synoptic_telemetry(lat=lat, lon=lon, scs_cn=scs_cn)


ml_controller = MLController()
