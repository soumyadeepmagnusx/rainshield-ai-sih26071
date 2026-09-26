"""
Feature Engineering & Physics-Informed Hydrological Transformations
for RAINSHIELD-AI v6.0 (SIH26071 - Ministry of Earth Sciences).
"""
import math
from typing import Dict, List

RAW_FEATURE_COLUMNS = [
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
    "tidal_backwater_level_m"
]

ENGINEERED_FEATURE_NAMES = RAW_FEATURE_COLUMNS + [
    "marshall_palmer_radar_rain_mm_hr",
    "insat_ir_cooling_index",
    "scs_potential_retention_s_mm",
    "scs_physics_direct_runoff_mm",
    "net_hydrological_surplus_mm"
]


def extract_engineered_features(row: Dict[str, float]) -> List[float]:
    """
    Transforms a raw sensor observation dictionary into an 18-dimensional
    physics-informed feature vector combining satellite, radar, AWS, NWP, and SCS-CN hydrology.
    """
    bt_k = float(row["insat_3ds_tir1_bt_k"])
    gsmap = float(row["gsmap_isro_rain_mm_hr"])
    dbz = float(row["imd_dwr_reflectivity_dbz"])
    vel = float(row["dwr_radial_velocity_m_s"])
    aws = float(row["aws_ground_gauge_mm_hr"])
    nwp = float(row["ncmrwf_nwp_1km_mm_hr"])
    ant_3h = float(row["antecedent_rain_3h_mm"])
    cn = max(35.0, min(99.0, float(row["scs_curve_number"])))
    soil = float(row["soil_moisture_saturation_pct"])
    elev = float(row["dem_elevation_m"])
    twi = float(row["topographic_wetness_index"])
    drain = float(row["drainage_efficiency_pct"])
    tidal = float(row["tidal_backwater_level_m"])

    # Physics Feature 1: Marshall-Palmer Radar Z-R Rain Rate (Z = 200 * R^1.6)
    z_lin = 10.0 ** (dbz / 10.0)
    mp_rain = (z_lin / 200.0) ** (1.0 / 1.6)

    # Physics Feature 2: INSAT-3DS Deep Convective Cloud-Top Cooling Index
    ir_cooling = max(0.0, 275.0 - bt_k)

    # Physics Feature 3 & 4: USDA-NRSC SCS Curve Number Retention (S) & Direct Runoff (Q)
    s_mm = (25400.0 / cn) - 254.0
    ia = 0.2 * s_mm
    p_eff = 0.40 * aws + 0.30 * mp_rain + 0.15 * gsmap + 0.15 * nwp + 0.22 * ant_3h
    if p_eff > ia:
        scs_q = ((p_eff - ia) ** 2) / (p_eff + 0.8 * s_mm)
    else:
        scs_q = 0.0

    # Physics Feature 5: Net Hydrological Surplus after Municipal Drainage & Pumping
    drain_cap_mm = (drain / 100.0) * 42.0
    net_surplus = max(0.0, scs_q - drain_cap_mm)

    return [
        bt_k, gsmap, dbz, vel, aws, nwp, ant_3h, cn, soil, elev, twi, drain, tidal,
        mp_rain, ir_cooling, s_mm, scs_q, net_surplus
    ]
