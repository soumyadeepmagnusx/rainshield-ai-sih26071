#!/usr/bin/env python3
"""
End-to-End Machine Learning Training & Evaluation Pipeline for RAINSHIELD-AI v6.0
Problem Statement: SIH26071 (Ministry of Earth Sciences)

1. Verifies/Generates the 2,400-row training dataset and 400-row validation dataset.
2. Trains the Multi-Modal Hydro-Meteorological Ensemble Model.
3. Computes meteorological verification scores (POD, FAR, CSI, RMSE, MAE, R2, Brier Score).
4. Saves trained model weights, SHAP importances, and evaluation metrics to `ml_pipeline/artifacts/`.
"""
import csv
import json
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from ml_pipeline.generate_training_data import generate_all_datasets
from ml_pipeline.models.ensemble_regressor import MultiModalFloodEnsembleModel


def _load_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _evaluate_predictions(rows: List[Dict[str, Any]], model: MultiModalFloodEnsembleModel) -> Dict[str, Any]:
    n = len(rows)
    sq_err_rain = 0.0
    abs_err_rain = 0.0
    sq_err_depth = 0.0
    abs_err_depth = 0.0

    y_true_depth = [float(r["target_inundation_depth_m"]) for r in rows]
    mean_depth = sum(y_true_depth) / max(1, n)
    ss_tot_depth = sum((y - mean_depth) ** 2 for y in y_true_depth) or 1.0

    # Contingency table for high-risk flood warning (ORANGE / RED >= 0.60m inundation)
    hits = 0
    false_alarms = 0
    misses = 0
    correct_negatives = 0
    exact_class_matches = 0
    brier_sum = 0.0

    for r in rows:
        pred = model.predict_row(r)
        true_r = float(r["target_fused_rain_mm_hr"])
        true_d = float(r["target_inundation_depth_m"])
        true_c = int(r["target_alert_class"])

        er_r = pred["predicted_fused_rain_mm_hr"] - true_r
        er_d = pred["predicted_inundation_depth_m"] - true_d

        sq_err_rain += er_r ** 2
        abs_err_rain += abs(er_r)
        sq_err_depth += er_d ** 2
        abs_err_depth += abs(er_d)

        if pred["predicted_alert_class"] == true_c:
            exact_class_matches += 1

        obs_event = true_c >= 2
        pred_event = pred["predicted_alert_class"] >= 2
        if obs_event and pred_event:
            hits += 1
        elif (not obs_event) and pred_event:
            false_alarms += 1
        elif obs_event and (not pred_event):
            misses += 1
        else:
            correct_negatives += 1

        prob_event = min(0.99, max(0.01, 1.0 / (1.0 + math.exp(-6.5 * (pred["predicted_inundation_depth_m"] - 0.60)))))
        brier_sum += (prob_event - (1.0 if obs_event else 0.0)) ** 2

    rmse_rain = math.sqrt(sq_err_rain / n)
    mae_rain = abs_err_rain / n
    rmse_depth = math.sqrt(sq_err_depth / n)
    mae_depth = abs_err_depth / n
    r2_depth = max(0.0, 1.0 - (sq_err_depth / ss_tot_depth))

    pod = hits / max(1, hits + misses)
    far = false_alarms / max(1, hits + false_alarms)
    csi = hits / max(1, hits + misses + false_alarms)
    brier = brier_sum / n

    return {
        "samples_evaluated": n,
        "rainfall_rmse_mm_hr": round(rmse_rain, 3),
        "rainfall_mae_mm_hr": round(mae_rain, 3),
        "inundation_depth_rmse_m": round(rmse_depth, 4),
        "inundation_depth_mae_m": round(mae_depth, 4),
        "inundation_r2_score": round(r2_depth, 4),
        "multiclass_accuracy_pct": round((exact_class_matches / n) * 100.0, 2),
        "probability_of_detection_pod": round(pod, 4),
        "false_alarm_ratio_far": round(far, 4),
        "critical_success_index_csi": round(csi, 4),
        "brier_skill_score": round(brier, 4),
        "contingency_matrix": {
            "hits": hits,
            "false_alarms": false_alarms,
            "misses": misses,
            "correct_negatives": correct_negatives
        }
    }


def run_training_pipeline(force_regenerate_data: bool = False) -> Dict[str, Any]:
    t0 = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(base_dir, "datasets")
    artifacts_dir = os.path.join(base_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    train_csv = os.path.join(datasets_dir, "imd_moes_multimodal_flood_training_2018_2025.csv")
    val_csv = os.path.join(datasets_dir, "historical_flood_validation_benchmarks.csv")

    if force_regenerate_data or (not os.path.exists(train_csv)) or (not os.path.exists(val_csv)):
        generate_all_datasets()

    train_rows = _load_csv(train_csv)
    val_rows = _load_csv(val_csv)

    model = MultiModalFloodEnsembleModel()
    model.fit(train_rows)

    train_metrics = _evaluate_predictions(train_rows, model)
    val_metrics = _evaluate_predictions(val_rows, model)
    shap_ranking = model.compute_shap_importances()

    duration_ms = round((time.time() - t0) * 1000.0, 1)
    run_id = f"TRN-SIH26071-{int(time.time())}"
    now_iso = datetime.now(timezone.utc).isoformat()

    model_artifact_path = os.path.join(artifacts_dir, "rainshield_trained_model.json")
    metrics_artifact_path = os.path.join(artifacts_dir, "evaluation_metrics_report.json")
    shap_artifact_path = os.path.join(artifacts_dir, "shap_feature_importances.json")

    with open(model_artifact_path, "w", encoding="utf-8") as f:
        json.dump(model.to_dict(), f, indent=2)

    with open(shap_artifact_path, "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "timestamp_utc": now_iso, "shap_ranking": shap_ranking}, f, indent=2)

    full_report = {
        "run_id": run_id,
        "timestamp_utc": now_iso,
        "training_duration_ms": duration_ms,
        "problem_statement_id": "SIH26071",
        "model_architecture": "Hybrid Multi-Modal Ridge Hydrological Regressor + 20-Stage Gradient Boosted Decision Stumps",
        "training_dataset": {
            "filename": "ml_pipeline/datasets/imd_moes_multimodal_flood_training_2018_2025.csv",
            "records": len(train_rows),
            "features_count": len(model.feature_names),
            "basins": ["GRID-MUM-01", "GRID-CHE-04", "GRID-GUW-02", "GRID-WAY-03", "GRID-DEL-05", "GRID-KOL-06"]
        },
        "validation_dataset": {
            "filename": "ml_pipeline/datasets/historical_flood_validation_benchmarks.csv",
            "records": len(val_rows)
        },
        "training_metrics": train_metrics,
        "validation_metrics": val_metrics,
        "top_shap_features": shap_ranking[:8]
    }

    with open(metrics_artifact_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    return full_report


if __name__ == "__main__":
    report = run_training_pipeline(force_regenerate_data=True)
    print(f"[ML-PIPELINE] Training Run Completed: {report['run_id']} in {report['training_duration_ms']} ms")
    print(f"[ML-PIPELINE] Training Set ({report['training_dataset']['records']} rows) -> R2: {report['training_metrics']['inundation_r2_score']}, CSI: {report['training_metrics']['critical_success_index_csi']}")
    print(f"[ML-PIPELINE] Holdout Validation ({report['validation_dataset']['records']} rows) -> POD: {report['validation_metrics']['probability_of_detection_pod']}, FAR: {report['validation_metrics']['false_alarm_ratio_far']}, CSI: {report['validation_metrics']['critical_success_index_csi']}, R2: {report['validation_metrics']['inundation_r2_score']}")
