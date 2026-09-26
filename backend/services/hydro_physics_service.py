"""
Hydrological Physics & CAP v1.2 XML Generation Service
for RAINSHIELD-AI v6.0 (SIH26071 - Ministry of Earth Sciences).
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

IST = timezone(timedelta(hours=5, minutes=30))


class HydroPhysicsService:
    def compute_scs_cn_inundation(
        self,
        rain_mm_hr: float,
        curve_number: float,
        drainage_efficiency_pct: float
    ) -> Dict[str, Any]:
        cn = max(30.0, min(99.0, float(curve_number)))
        s_mm = (25400.0 / cn) - 254.0
        ia_mm = 0.2 * s_mm
        p_effective = float(rain_mm_hr) * 2.2

        if p_effective > ia_mm:
            runoff_q = ((p_effective - ia_mm) ** 2) / (p_effective + 0.8 * s_mm)
        else:
            runoff_q = 0.0

        infiltration_loss = max(0.0, p_effective - runoff_q)
        drain_capacity_mm = (float(drainage_efficiency_pct) / 100.0) * 65.0
        net_accumulation_mm = max(0.0, runoff_q - drain_capacity_mm)
        predicted_depth_m = round(min(4.5, (net_accumulation_mm / 1000.0) * 18.5 + (0.12 if rain_mm_hr > 30 else 0.0)), 2)

        if predicted_depth_m >= 1.2:
            alert = "RED"
            risk_score = min(99, int(75 + (predicted_depth_m - 1.2) * 12))
        elif predicted_depth_m >= 0.6:
            alert = "ORANGE"
            risk_score = int(50 + (predicted_depth_m - 0.6) * 40)
        elif predicted_depth_m >= 0.25:
            alert = "YELLOW"
            risk_score = int(25 + (predicted_depth_m - 0.25) * 65)
        else:
            alert = "GREEN"
            risk_score = max(5, int(predicted_depth_m * 80))

        return {
            "status": "ok",
            "inputs": {
                "rain_mm_hr": round(rain_mm_hr, 1),
                "curve_number": round(cn, 1),
                "drainage_efficiency_pct": round(drainage_efficiency_pct, 1)
            },
            "physics": {
                "potential_retention_s_mm": round(s_mm, 1),
                "initial_abstraction_ia_mm": round(ia_mm, 1),
                "effective_storm_precip_mm": round(p_effective, 1),
                "direct_runoff_q_mm": round(runoff_q, 1),
                "infiltration_loss_mm": round(infiltration_loss, 1),
                "drainage_removal_mm": round(drain_capacity_mm, 1),
                "net_surface_accumulation_mm": round(net_accumulation_mm, 1),
                "predicted_inundation_depth_m": predicted_depth_m,
                "alert_level": alert,
                "composite_risk_score": risk_score
            }
        }

    def generate_cap_xml(self, grid: Dict[str, Any]) -> str:
        now = datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30")
        expires = (datetime.now(IST) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S+05:30")
        severity_map = {"RED": "Extreme", "ORANGE": "Severe", "YELLOW": "Moderate", "GREEN": "Minor"}
        urgency_map = {"RED": "Immediate", "ORANGE": "Expected", "YELLOW": "Future", "GREEN": "Past"}

        gid = grid.get("id") or grid.get("grid_id", "GRID-MUM-01")
        alert_lvl = grid.get("alert_color", grid.get("alert_level", "RED"))
        sev = severity_map.get(alert_lvl, "Severe")
        urg = urgency_map.get(alert_lvl, "Immediate")
        s = grid.get("sources", {})
        depth_m = grid.get("predicted_inundation_depth_m", 1.85)
        unc_m = grid.get("ensemble_uncertainty_m", 0.18)
        fused_r = grid.get("fused_rainfall_mm_hr", 107.0)
        rec_actions = grid.get("recommended_actions", ["Evacuate low-lying zones immediately"])

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>MOES-IMD-RAINSHIELD-{gid}-{int(datetime.now().timestamp())}</identifier>
  <sender>earlywarning-moes@gov.in</sender>
  <sent>{now}</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <code_sih>SIH26071-MoES-RainshieldAI-v6.0</code_sih>
  <info>
    <language>en-IN</language>
    <category>Met</category>
    <event>Heavy Rainfall and Urban Flash Flood Inundation</event>
    <responseType>Evacuate</responseType>
    <urgency>{urg}</urgency>
    <severity>{sev}</severity>
    <certainty>Observed</certainty>
    <effective>{now}</effective>
    <expires>{expires}</expires>
    <senderName>Ministry of Earth Sciences (MoES) / IMD / NDMA Integrated Command</senderName>
    <headline>{alert_lvl} ALERT: {grid.get('name', gid)} - Predicted Inundation {depth_m}m</headline>
    <description>Multi-source AI fusion (INSAT-3DS TIR-1 {s.get('insat_3ds_tir_k', 194.0)}K, IMD DWR {s.get('imd_dwr_dbz', 64.0)} dBZ, AWS {s.get('aws_gauge_mm_hr', 106.3)} mm/hr, NWP {s.get('nwp_downscaled_1km_mm_hr', 104.2)} mm/hr) indicates fused rainfall rate of {fused_r} mm/hr. 2D hydrodynamic surrogate projects {depth_m}m (+/- {unc_m}m) inundation depth.</description>
    <instruction>{'; '.join(rec_actions)}</instruction>
    <area>
      <areaDesc>{grid.get('name', gid)}, {grid.get('state', 'India')}</areaDesc>
    </area>
  </info>
</alert>"""


hydro_service = HydroPhysicsService()
