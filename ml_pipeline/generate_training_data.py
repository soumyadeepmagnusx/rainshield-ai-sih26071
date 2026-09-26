#!/usr/bin/env python3
"""
Generates the Multi-Source Meteorological & 2D Inundation Training and Holdout Datasets
for SIH26071 (Ministry of Earth Sciences - RAINSHIELD-AI v6.0).

Datasets produced:
1. ml_pipeline/datasets/imd_moes_multimodal_flood_training_2018_2025.csv (2,400 records)
2. ml_pipeline/datasets/historical_flood_validation_benchmarks.csv (400 records)
"""
import csv
import math
import os
import random
from datetime import datetime, timedelta

BASIN_PROFILES = [
    {
        "basin_id": "GRID-MUM-01",
        "city": "Mumbai",
        "base_cn": 91.0,
        "dem_elev_m": 4.2,
        "twi": 14.8,
        "coastal": True,
        "regimes": ["Arabian_Sea_Monsoon_Surge", "Offshore_Trough_Cloudburst", "Mesoscale_Convective_System", "Moderate_Monsoon_Spell"]
    },
    {
        "basin_id": "GRID-CHE-04",
        "city": "Chennai",
        "base_cn": 89.5,
        "dem_elev_m": 5.8,
        "twi": 13.9,
        "coastal": True,
        "regimes": ["Bay_of_Bengal_Cyclonic_Landfall", "Northeast_Monsoon_Depression", "Coastal_Squall_Line", "Stratiform_Monsoon_Rain"]
    },
    {
        "basin_id": "GRID-GUW-02",
        "city": "Guwahati",
        "base_cn": 86.0,
        "dem_elev_m": 51.4,
        "twi": 13.2,
        "coastal": False,
        "regimes": ["Meghalaya_Orographic_Cloudburst", "Brahmaputra_Trough_Convection", "Pre_Monsoon_Norwester", "Valley_Monsoon_Shower"]
    },
    {
        "basin_id": "GRID-WAY-03",
        "city": "Wayanad-Kozhikode",
        "base_cn": 84.5,
        "dem_elev_m": 780.0,
        "twi": 15.1,
        "coastal": False,
        "regimes": ["Western_Ghats_Orographic_Surge", "Low_Level_Jet_Extreme_Rain", "Monsoon_Vortex_Feeder_Band", "Light_Orographic_Spell"]
    },
    {
        "basin_id": "GRID-DEL-05",
        "city": "New Delhi",
        "base_cn": 88.0,
        "dem_elev_m": 212.0,
        "twi": 11.6,
        "coastal": False,
        "regimes": ["Western_Disturbance_Monsoon_Interaction", "Urban_Heat_Island_Downpour", "Yamuna_Catchment_Surge", "Scattered_Convective_Cell"]
    },
    {
        "basin_id": "GRID-KOL-06",
        "city": "Kolkata",
        "base_cn": 90.0,
        "dem_elev_m": 6.1,
        "twi": 14.3,
        "coastal": True,
        "regimes": ["Gangetic_West_Bengal_Deep_Depression", "Bay_Cyclone_Spiral_Band", "Hooghly_Spring_Tide_Downpour", "Monsoon_Trough_Pass"]
    }
]

FIELDNAMES = [
    "record_id",
    "timestamp_utc",
    "basin_id",
    "synoptic_regime",
    "insat_3ds_tir1_bt_k",
    "gsmap_isro_rain_mm_hr",
    "imd_dwr_reflectivity_dbz",
    "dwr_radial_velocity_m_s",
    "aws_ground_gauge_mm_hr",
    "ncmrwf_nwp_1km_mm_hr",
    "antecedent_rain_3h_mm",
    "scs_curve_number",
    "soil_moisture_saturation_pct",
    "dem_elevation_m",
    "topographic_wetness_index",
    "drainage_efficiency_pct",
    "tidal_backwater_level_m",
    "target_fused_rain_mm_hr",
    "target_runoff_mm_hr",
    "target_inundation_depth_m",
    "target_alert_class"
]


def _simulate_row(idx: int, prefix: str, rng: random.Random, base_time: datetime) -> dict:
    profile = BASIN_PROFILES[idx % len(BASIN_PROFILES)]
    # Draw severity tier so training data has balanced representation from light rain to extreme cloudbursts
    tier = rng.choices([0, 1, 2, 3], weights=[0.28, 0.27, 0.25, 0.20])[0]
    if tier == 0:
        true_rain = rng.uniform(2.0, 22.0)
        antecedent_3h = rng.uniform(0.0, 35.0)
        soil_sat = rng.uniform(35.0, 65.0)
        drainage_eff = rng.uniform(68.0, 92.0)
    elif tier == 1:
        true_rain = rng.uniform(22.0, 48.0)
        antecedent_3h = rng.uniform(25.0, 85.0)
        soil_sat = rng.uniform(58.0, 82.0)
        drainage_eff = rng.uniform(52.0, 78.0)
    elif tier == 2:
        true_rain = rng.uniform(48.0, 85.0)
        antecedent_3h = rng.uniform(65.0, 165.0)
        soil_sat = rng.uniform(75.0, 93.0)
        drainage_eff = rng.uniform(35.0, 62.0)
    else:
        true_rain = rng.uniform(85.0, 158.0)
        antecedent_3h = rng.uniform(130.0, 310.0)
        soil_sat = rng.uniform(88.0, 99.5)
        drainage_eff = rng.uniform(18.0, 48.0)

    # 1. INSAT-3DS TIR-1 Cloud-Top Brightness Temperature (K) & GSMaP-ISRO rain rate
    insat_bt_k = max(188.0, min(290.0, 278.0 - 0.62 * true_rain + rng.gauss(0, 3.2)))
    gsmap_rain = max(0.0, true_rain * rng.uniform(0.86, 1.12) + rng.gauss(0, 2.4))

    # 2. IMD S-Band Doppler Weather Radar (Marshall-Palmer Z = 200 * R^1.6 -> dBZ = 10*log10(Z))
    z_linear = max(1.0, 200.0 * (max(0.5, true_rain) ** 1.6))
    dwr_dbz = min(66.5, max(12.0, 10.0 * math.log10(z_linear) + rng.gauss(0, 1.4)))
    dwr_vel = round(8.0 + 0.24 * true_rain + rng.gauss(0, 2.1), 2)

    # 3. IMD AWS / ARG Tipping-Bucket Ground Gauge (closest to ground truth with wind-undercatch noise)
    aws_rain = max(0.0, true_rain * rng.uniform(0.94, 1.05) + rng.gauss(0, 1.5))

    # 4. NCMRWF / IMD GFS 1km Downscaled NWP Forecast
    nwp_rain = max(0.0, true_rain * rng.uniform(0.82, 1.16) + rng.gauss(0, 3.8))

    # Ground-truth bias-corrected multi-source fused rainfall
    fused_rain = (
        0.38 * aws_rain
        + 0.32 * ((10.0 ** (dwr_dbz / 10.0) / 200.0) ** (1.0 / 1.6))
        + 0.16 * gsmap_rain
        + 0.14 * nwp_rain
    )

    # Hydrological SCS-CN Direct Surface Runoff (USDA-NRSC formulation)
    cn = min(98.0, max(55.0, profile["base_cn"] + (soil_sat - 65.0) * 0.12 + rng.gauss(0, 0.8)))
    s_retention = (25400.0 / cn) - 254.0
    ia = 0.2 * s_retention
    eff_precip = fused_rain + 0.22 * antecedent_3h
    if eff_precip > ia:
        runoff_q = ((eff_precip - ia) ** 2) / (eff_precip + 0.8 * s_retention)
    else:
        runoff_q = 0.0

    # Coastal tidal stage (m)
    tidal_m = round(rng.uniform(1.2, 4.6) if profile["coastal"] else rng.uniform(0.0, 0.4), 2)

    # 2D Shallow-Water Surrogate Inundation Depth (m)
    twi = round(profile["twi"] + rng.gauss(0, 0.35), 2)
    drainage_drain_mm_hr = (drainage_eff / 100.0) * 42.0
    net_ponding_mm = max(0.0, runoff_q - drainage_drain_mm_hr)
    tidal_penalty = max(0.0, (tidal_m - 2.2) * 0.18) if profile["coastal"] else 0.0
    depth_m = (
        0.0145 * net_ponding_mm
        + 0.0028 * antecedent_3h
        + 0.045 * max(0.0, twi - 11.0)
        + tidal_penalty
        + rng.gauss(0, 0.03)
    )
    depth_m = round(max(0.02, min(3.85, depth_m)), 3)

    # Alert Severity Class (0=GREEN, 1=YELLOW, 2=ORANGE, 3=RED)
    if depth_m >= 1.15:
        alert_class = 3
    elif depth_m >= 0.60:
        alert_class = 2
    elif depth_m >= 0.25:
        alert_class = 1
    else:
        alert_class = 0

    obs_time = base_time + timedelta(hours=idx * 3)
    return {
        "record_id": f"{prefix}-{idx + 1:04d}",
        "timestamp_utc": obs_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "basin_id": profile["basin_id"],
        "synoptic_regime": profile["regimes"][tier],
        "insat_3ds_tir1_bt_k": round(insat_bt_k, 2),
        "gsmap_isro_rain_mm_hr": round(gsmap_rain, 2),
        "imd_dwr_reflectivity_dbz": round(dwr_dbz, 2),
        "dwr_radial_velocity_m_s": round(dwr_vel, 2),
        "aws_ground_gauge_mm_hr": round(aws_rain, 2),
        "ncmrwf_nwp_1km_mm_hr": round(nwp_rain, 2),
        "antecedent_rain_3h_mm": round(antecedent_3h, 2),
        "scs_curve_number": round(cn, 2),
        "soil_moisture_saturation_pct": round(soil_sat, 2),
        "dem_elevation_m": round(profile["dem_elev_m"], 2),
        "topographic_wetness_index": twi,
        "drainage_efficiency_pct": round(drainage_eff, 2),
        "tidal_backwater_level_m": tidal_m,
        "target_fused_rain_mm_hr": round(fused_rain, 2),
        "target_runoff_mm_hr": round(runoff_q, 2),
        "target_inundation_depth_m": depth_m,
        "target_alert_class": alert_class
    }


def generate_all_datasets() -> dict:
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")
    os.makedirs(base_dir, exist_ok=True)

    train_path = os.path.join(base_dir, "imd_moes_multimodal_flood_training_2018_2025.csv")
    val_path = os.path.join(base_dir, "historical_flood_validation_benchmarks.csv")

    rng_train = random.Random(26071)
    start_train = datetime(2018, 6, 1, 0, 0, 0)
    with open(train_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for i in range(2400):
            writer.writerow(_simulate_row(i, "MOES-TRN", rng_train, start_train))

    rng_val = random.Random(99071)
    start_val = datetime(2023, 12, 1, 0, 0, 0)
    with open(val_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for i in range(400):
            writer.writerow(_simulate_row(i, "MOES-VAL", rng_val, start_val))

    return {
        "training_csv": train_path,
        "training_rows": 2400,
        "validation_csv": val_path,
        "validation_rows": 400
    }


if __name__ == "__main__":
    info = generate_all_datasets()
    print(f"[ML-DATA] Generated {info['training_rows']} training rows -> {info['training_csv']}")
    print(f"[ML-DATA] Generated {info['validation_rows']} validation rows -> {info['validation_csv']}")
