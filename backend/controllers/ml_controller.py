"""
Machine Learning Dataset, Training Metrics, Live Retraining & Database Overview Controller
for RAINSHIELD-AI v6.0 (SIH26071 - Ministry of Earth Sciences).
"""
from typing import Any, Dict

from backend.database.db_manager import db_instance
from backend.services.ml_inference_service import ml_service


class MLController:
    def get_ml_and_db_dashboard(self) -> Dict[str, Any]:
        ml_info = ml_service.get_training_report_and_dataset_preview(sample_limit=12)
        db_info = db_instance.get_database_overview()
        return {
            "status": "ok",
            "database_overview": db_info,
            "ml_pipeline": ml_info
        }

    def trigger_retrain(self) -> Dict[str, Any]:
        res = ml_service.trigger_live_retrain()
        res["database_overview"] = db_instance.get_database_overview()
        return res

    def predict_custom(self, body: Dict[str, Any]) -> Dict[str, Any]:
        pred = ml_service.predict_from_features(body)
        return {"status": "ok", "prediction": pred}


ml_controller = MLController()
