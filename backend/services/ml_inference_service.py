"""
Machine Learning Inference & Dataset Inspection Service
for RAINSHIELD-AI v6.0 (SIH26071 - Ministry of Earth Sciences).
"""
import csv
import json
import os
from typing import Any, Dict, List

from backend.config.settings import AppConfig
from backend.database.db_manager import db_instance
from ml_pipeline.models.ensemble_regressor import MultiModalFloodEnsembleModel
from ml_pipeline.train_pipeline import run_training_pipeline


class MLInferenceService:
    def __init__(self) -> None:
        self.model: MultiModalFloodEnsembleModel = self._load_or_train_model()

    def _load_or_train_model(self) -> MultiModalFloodEnsembleModel:
        if not os.path.exists(AppConfig.TRAINED_MODEL_JSON) or not os.path.exists(AppConfig.EVAL_METRICS_JSON):
            report = run_training_pipeline(force_regenerate_data=True)
            db_instance.record_ml_training_run(report)

        with open(AppConfig.TRAINED_MODEL_JSON, "r", encoding="utf-8") as f:
            model_dict = json.load(f)
        return MultiModalFloodEnsembleModel.from_dict(model_dict)

    def get_training_report_and_dataset_preview(self, sample_limit: int = 15) -> Dict[str, Any]:
        if not os.path.exists(AppConfig.EVAL_METRICS_JSON):
            report = run_training_pipeline(force_regenerate_data=False)
            db_instance.record_ml_training_run(report)
        else:
            with open(AppConfig.EVAL_METRICS_JSON, "r", encoding="utf-8") as f:
                report = json.load(f)

        train_samples: List[Dict[str, Any]] = []
        if os.path.exists(AppConfig.TRAIN_DATASET_CSV):
            with open(AppConfig.TRAIN_DATASET_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    if idx >= sample_limit:
                        break
                    train_samples.append(row)

        val_samples: List[Dict[str, Any]] = []
        if os.path.exists(AppConfig.VAL_DATASET_CSV):
            with open(AppConfig.VAL_DATASET_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    if idx >= 8:
                        break
                    val_samples.append(row)

        schema_meta = {}
        if os.path.exists(AppConfig.DATASET_METADATA_JSON):
            with open(AppConfig.DATASET_METADATA_JSON, "r", encoding="utf-8") as f:
                schema_meta = json.load(f)

        return {
            "status": "ok",
            "evaluation_report": report,
            "dataset_metadata": schema_meta,
            "training_csv_preview": train_samples,
            "validation_csv_preview": val_samples
        }

    def trigger_live_retrain(self) -> Dict[str, Any]:
        report = run_training_pipeline(force_regenerate_data=False)
        with open(AppConfig.TRAINED_MODEL_JSON, "r", encoding="utf-8") as f:
            self.model = MultiModalFloodEnsembleModel.from_dict(json.load(f))
        db_instance.record_ml_training_run(report)
        return {
            "status": "ok",
            "message": "Model successfully retrained on 2,400 multi-modal meteorological records and validated on 400 benchmark records.",
            "report": report
        }

    def predict_from_features(self, row_features: Dict[str, Any]) -> Dict[str, Any]:
        return self.model.predict_row(row_features)


ml_service = MLInferenceService()
