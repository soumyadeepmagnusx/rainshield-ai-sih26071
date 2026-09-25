"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Satellite,
  Radar,
  Waves,
  CloudRain,
  Cpu,
  Radio,
  AlertTriangle,
  ShieldAlert,
  Send,
  MapPin,
  Clock,
  Activity,
  Volume2,
  CheckCircle2,
  ChevronRight,
  Layers,
  Navigation,
  X,
  Sliders,
  Sparkles,
  RefreshCw,
} from "lucide-react";

// ==================== TYPES & MOCK TELEMETRY ====================
interface Hotspot {
  id: string;
  zoneCode: string;
  name: string;
  xPct: number;
  yPct: number;
  riskPct: number;
  severity: "RED" | "AMBER" | "EMERALD";
  predictedDepthM: number;
  rainRateMmHr: number;
  exposedPop: number;
  demElevationM: number;
  drainStatus: string;
  recommendedAction: string;
}

const HOTSPOTS: Hotspot[] = [
  {
    id: "hs-1",
    zoneCode: "ZONE-A",
    name: "Mumbai — Mithi Basin & Kurla Bail Bazaar",
    xPct: 44,
    yPct: 52,
    riskPct: 94,
    severity: "RED",
    predictedDepthM: 1.42,
    rainRateMmHr: 79.4,
    exposedPop: 145000,
    demElevationM: 6.4,
    drainStatus: "Tide-Locked (94% Capacity)",
    recommendedAction:
      "Activate pumping stations at Haji Ali, Love Grove & Britannia Outfalls at 100% capacity",
  },
  {
    id: "hs-2",
    zoneCode: "ZONE-B",
    name: "Milan & Andheri Subway Catchment",
    xPct: 32,
    yPct: 36,
    riskPct: 89,
    severity: "RED",
    predictedDepthM: 1.15,
    rainRateMmHr: 74.2,
    exposedPop: 68000,
    demElevationM: 7.1,
    drainStatus: "Surcharge Overflow",
    recommendedAction:
      "Close Milan & Andheri subways; divert vehicular traffic to Eastern Express Highway",
  },
  {
    id: "hs-3",
    zoneCode: "ZONE-C",
    name: "Hindmata — Dadar Low-Lying Bowl",
    xPct: 58,
    yPct: 68,
    riskPct: 78,
    severity: "AMBER",
    predictedDepthM: 0.82,
    rainRateMmHr: 61.5,
    exposedPop: 52000,
    demElevationM: 8.2,
    drainStatus: "Pumps Active (78%)",
    recommendedAction:
      "Pre-position 4 NDRF flood rescue teams at Kurla Bail Bazaar & Hindmata clusters",
  },
  {
    id: "hs-4",
    zoneCode: "ZONE-D",
    name: "Eastern Express Elevated Corridor",
    xPct: 72,
    yPct: 34,
    riskPct: 18,
    severity: "EMERALD",
    predictedDepthM: 0.08,
    rainRateMmHr: 48.0,
    exposedPop: 4200,
    demElevationM: 19.5,
    drainStatus: "Free Flow (Clear)",
    recommendedAction:
      "Designate as primary green evacuation corridor for NDRF & emergency ambulances",
  },
];

const TIMELINE_DATA = Array.from({ length: 25 }, (_, h) => {
  const wave = Math.sin((h / 24) * Math.PI);
  const rainMm = +(28 + wave * 68 + (h > 4 && h < 12 ? 18 : 0)).toFixed(1);
  const depthM = +(0.35 + wave * 1.35).toFixed(2);
  return {
    hour: h,
    label: h === 0 ? "LIVE" : `+${h}h`,
    rainMm,
    depthM,
    upperCi: +(depthM + 0.18).toFixed(2),
    lowerCi: +Math.max(0.05, depthM - 0.18).toFixed(2),
  };
});

export default function RainshieldCyberCommandCenter() {
  const [clock, setClock] = useState<string>("22:15:00 IST");
  const [layers, setLayers] = useState({
    satellite: true,
    radar: true,
    inundation: true,
  });
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [scrubHour, setScrubHour] = useState<number>(4);
  const [isLoadingSkeleton, setIsLoadingSkeleton] = useState<boolean>(false);
  const [smsBroadcasted, setSmsBroadcasted] = useState<boolean>(false);
  const [evacDeployed, setEvacDeployed] = useState<boolean>(false);
  const [activeVoiceLang, setActiveVoiceLang] = useState<string | null>(null);

  // Live ticking telemetry states
  const [telemetry, setTelemetry] = useState({
    satCdi: 91.4,
    satLatency: 4,
    radarDbz: 58.4,
    radarLatency: 5,
    awsMmHr: 79.4,
    awsLatency: 3,
    nwpConf: 94.2,
    nwpLatency: 6,
  });

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setClock(
        now.toLocaleTimeString("en-IN", {
          hour12: false,
          timeZone: "Asia/Kolkata",
        }) + " IST"
      );
      setTelemetry((prev) => ({
        satCdi: +(91.0 + Math.random() * 1.8).toFixed(1),
        satLatency: Math.floor(4 + Math.random() * 3),
        radarDbz: +(57.8 + Math.random() * 1.6).toFixed(1),
        radarLatency: Math.floor(4 + Math.random() * 4),
        awsMmHr: +(78.6 + Math.random() * 2.2).toFixed(1),
        awsLatency: Math.floor(3 + Math.random() * 3),
        nwpConf: +(93.9 + Math.random() * 0.7).toFixed(1),
        nwpLatency: Math.floor(5 + Math.random() * 4),
      }));
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  const toggleLayer = (key: keyof typeof layers) => {
    setIsLoadingSkeleton(true);
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
    setTimeout(() => setIsLoadingSkeleton(false), 280);
  };

  const currentStep = TIMELINE_DATA[scrubHour] || TIMELINE_DATA[0];
  const floodExpansionScale = 0.75 + (currentStep.depthM / 1.7) * 0.65;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-cyan-500/30 overflow-x-hidden">
      {/* ==================== 1. COMMAND CENTER HEADER & LIVE TICKER ==================== */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-slate-950/90 border-b border-slate-800">
        <div className="max-w-[1600px] mx-auto px-4 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.25)]">
              <Radar className="w-5 h-5 text-cyan-400 animate-spin" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold tracking-wider text-base text-white">
                  RAINSHIELD-AI
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                  SIH26071
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  MINISTRY OF EARTH SCIENCES (MoES)
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                AI/ML Integrated Heavy Rainfall Early Warning &amp; 2D Inundation DSS
              </p>
            </div>
          </div>

          {/* Flashing Global Status Ticker */}
          <div className="hidden xl:flex items-center gap-3 flex-1 max-w-2xl bg-red-950/40 border border-red-500/40 rounded-lg px-3 py-1.5 overflow-hidden">
            <span className="flex items-center gap-1.5 text-xs font-mono font-bold text-red-400 shrink-0 animate-pulse">
              <AlertTriangle className="w-4 h-4" /> LIVE THREAT TICKER:
            </span>
            <div className="text-xs font-mono text-red-200 truncate">
              RED ALERT: Mumbai Urban Area (Mithi Basin) — Inundation Risk 94% (1.42m) •
              RED ALERT: Guwahati Bharalu Basin — Flash Flood Risk 92% •
              AMBER WATCH: Chennai Velachery Marsh — Risk 84%
            </div>
          </div>

          {/* Right Clock & System Pulse */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 font-mono text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-emerald-400 font-semibold">DEFCON-READY</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 font-mono text-xs text-cyan-300">
              <Clock className="w-3.5 h-3.5" />
              <span>{clock}</span>
            </div>
          </div>
        </div>
      </header>

      {/* ==================== MAIN DASHBOARD GRID ==================== */}
      <main className="max-w-[1600px] mx-auto p-4 grid grid-cols-12 gap-4">
        {/* ==================== 2. HERO GEOSPATIAL MAP SIMULATOR (8 COLS) ==================== */}
        <section className="col-span-12 lg:col-span-8 flex flex-col gap-4">
          <div className="relative h-[520px] rounded-xl backdrop-blur-md bg-slate-900/40 border border-slate-800 overflow-hidden shadow-2xl">
            {/* Simulated Geospatial Grid & Topographic Contours */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(15,23,42,0.4)_0%,rgba(2,6,23,0.95)_100%)]" />

            {/* Layer 1: Satellite Multi-Spectral Cloud Density Overlay */}
            <AnimatePresence>
              {layers.satellite && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.65 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_44%_52%,rgba(168,85,247,0.35),rgba(59,130,246,0.18)_45%,transparent_75%)]"
                />
              )}
            </AnimatePresence>

            {/* Layer 2: Doppler Radar Rotating Sweep & dBZ Rings */}
            <AnimatePresence>
              {layers.radar && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 pointer-events-none flex items-center justify-center"
                >
                  <div className="w-[420px] h-[420px] rounded-full border border-cyan-500/20 relative">
                    <div className="
                      absolute inset-8 rounded-full border border-cyan-500/20
                    " />
                    <div className="
                      absolute inset-20 rounded-full border border-red-500/30
                    " />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Layer 3: AI Inundation Prediction Model Polygons (Scales with 24h Slider!) */}
            <AnimatePresence>
              {layers.inundation &&
                HOTSPOTS.map((hs) => (
                  <motion.div
                    key={hs.id}
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{
                      scale: floodExpansionScale,
                      opacity: 0.85,
                    }}
                    exit={{ scale: 0.5, opacity: 0 }}
                    style={{ left: `${hs.xPct}%`, top: `${hs.yPct}%` }}
                    className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none"
                  >
                    <div
                      className={`w-36 h-36 rounded-full blur-md ${
                        hs.severity === "RED"
                          ? "bg-red-500/35 border border-red-500/60"
                          : hs.severity === "AMBER"
                          ? "bg-amber-500/30 border border-amber-500/60"
                          : "bg-emerald-500/25 border border-emerald-500/50"
                      }`}
                    />
                  </motion.div>
                ))}
            </AnimatePresence>

            {/* Interactive Floating Layer Toggle Buttons (Left Side) */}
            <div className="absolute top-4 left-4 z-20 flex flex-col gap-2">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 bg-slate-950/80 px-2.5 py-1 rounded border border-slate-800">
                Geospatial Data Layers
              </div>
              <button
                onClick={() => toggleLayer("satellite")}
                className={`flex items-center gap-2.5 px-3.5 py-2 rounded-lg font-mono text-xs border transition-all ${
                  layers.satellite
                    ? "bg-purple-500/20 border-purple-400 text-purple-200 shadow-[0_0_15px_rgba(168,85,247,0.3)]"
                    : "bg-slate-900/80 border-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <Satellite className="w-4 h-4" />
                <span>🛰️ Satellite Overlay</span>
              </button>

              <button
                onClick={() => toggleLayer("radar")}
                className={`flex items-center gap-2.5 px-3.5 py-2 rounded-lg font-mono text-xs border transition-all ${
                  layers.radar
                    ? "bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                    : "bg-slate-900/80 border-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <Radar className="w-4 h-4" />
                <span>📡 Doppler Radar Feed</span>
              </button>

              <button
                onClick={() => toggleLayer("inundation")}
                className={`flex items-center gap-2.5 px-3.5 py-2 rounded-lg font-mono text-xs border transition-all ${
                  layers.inundation
                    ? "bg-red-500/20 border-red-400 text-red-200 shadow-[0_0_15px_rgba(239,68,68,0.3)]"
                    : "bg-slate-900/80 border-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <Waves className="w-4 h-4" />
                <span>🌊 AI Inundation Prediction Model</span>
              </button>
            </div>

            {/* Clickable Pulsing Hot-Spots */}
            {HOTSPOTS.map((hs) => (
              <button
                key={hs.id}
                onClick={() => setSelectedHotspot(hs)}
                style={{ left: `${hs.xPct}%`, top: `${hs.yPct}%` }}
                className="absolute -translate-x-1/2 -translate-y-1/2 z-20 group focus:outline-none"
              >
                <span
                  className={`absolute -inset-3 rounded-full animate-ping opacity-60 ${
                    hs.severity === "RED"
                      ? "bg-red-500"
                      : hs.severity === "AMBER"
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                  }`}
                />
                <div
                  className={`relative px-2.5 py-1 rounded-md font-mono text-[11px] font-bold flex items-center gap-1.5 border shadow-lg transition-transform group-hover:scale-110 ${
                    hs.severity === "RED"
                      ? "bg-red-950/90 border-red-400 text-red-200"
                      : hs.severity === "AMBER"
                      ? "bg-amber-950/90 border-amber-400 text-amber-200"
                      : "bg-emerald-950/90 border-emerald-400 text-emerald-200"
                  }`}
                >
                  <MapPin className="w-3.5 h-3.5" />
                  <span>
                    {hs.zoneCode}: {hs.riskPct}%
                  </span>
                </div>
              </button>
            ))}

            {/* Skeleton Loader Shimmer on Layer Switch */}
            {isLoadingSkeleton && (
              <div className="absolute top-4 right-4 z-30 bg-slate-900/90 border border-cyan-500/40 rounded-lg px-3 py-2 flex items-center gap-2 font-mono text-xs text-cyan-300 animate-pulse">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Re-computing 1km Spatial Tensor...</span>
              </div>
            )}
          </div>

          {/* ==================== 4. AI INUNDATION TIMELINE PREDICTOR (24H SCRUBBER) ==================== */}
          <div className="rounded-xl backdrop-blur-md bg-slate-900/40 border border-slate-800 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  AI Inundation Timeline Predictor (24-Hour Horizon)
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  Scrub forward to visualize ConvLSTM + 2D Shallow-Water flood expansion
                </p>
              </div>
              <div className="flex items-center gap-3 font-mono text-xs">
                <span className="px-2.5 py-1 rounded bg-cyan-500/15 border border-cyan-500/40 text-cyan-300">
                  HORIZON: {currentStep.label}
                </span>
                <span className="px-2.5 py-1 rounded bg-red-500/15 border border-red-500/40 text-red-300 font-bold">
                  PREDICTED DEPTH: {currentStep.depthM}m (±0.18m)
                </span>
              </div>
            </div>

            {/* Interactive Time Scrubber Slider */}
            <div className="mt-2">
              <input
                type="range"
                min={0}
                max={24}
                value={scrubHour}
                onChange={(e) => setScrubHour(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
              <div className="flex justify-between text-[11px] font-mono text-slate-400 mt-1">
                <span>LIVE (0h)</span>
                <span>+6h Nowcast</span>
                <span>+12h ConvLSTM</span>
                <span>+18h NWP-GNN</span>
                <span>+24h Forecast</span>
              </div>
            </div>
          </div>
        </section>

        {/* ==================== 3 & 5. TELEMETRY MONITOR + EARLY WARNING BROADCAST PANEL (4 COLS) ==================== */}
        <aside className="col-span-12 lg:col-span-4 flex flex-col gap-4">
          {/* 4 Live-Updating Telemetry Streams */}
          <div className="rounded-xl backdrop-blur-md bg-slate-900/40 border border-slate-800 p-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-white mb-3 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              Multi-Source Data Ingestion Monitor
            </h2>
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                  <span>SATELLITE FEED</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    CONNECTED
                  </span>
                </div>
                <div className="text-lg font-mono font-bold text-white mt-1">
                  {telemetry.satCdi} CDI
                </div>
                <div className="text-[10px] font-mono text-cyan-400 mt-1">
                  Latency: {telemetry.satLatency}ms delay
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                  <span>DOPPLER RADAR</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    CONNECTED
                  </span>
                </div>
                <div className="text-lg font-mono font-bold text-white mt-1">
                  {telemetry.radarDbz} dBZ
                </div>
                <div className="text-[10px] font-mono text-cyan-400 mt-1">
                  Latency: {telemetry.radarLatency}ms delay
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                  <span>AWS GAUGES</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    CONNECTED
                  </span>
                </div>
                <div className="text-lg font-mono font-bold text-white mt-1">
                  {telemetry.awsMmHr} mm/hr
                </div>
                <div className="text-[10px] font-mono text-cyan-400 mt-1">
                  Latency: {telemetry.awsLatency}ms delay
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                  <span>NWP MODELS</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    CONNECTED
                  </span>
                </div>
                <div className="text-lg font-mono font-bold text-white mt-1">
                  {telemetry.nwpConf}% CI
                </div>
                <div className="text-[10px] font-mono text-cyan-400 mt-1">
                  Latency: {telemetry.nwpLatency}ms delay
                </div>
              </div>
            </div>
          </div>

          {/* Early Warning Broadcast & Mitigation Panel */}
          <div className="rounded-xl backdrop-blur-md bg-slate-900/40 border border-slate-800 p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-400" />
                Early Warning Broadcast &amp; Mitigation
              </h2>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-red-500/20 border border-red-500/40 text-red-300 font-bold">
                145,000 Pop. Exposed
              </span>
            </div>

            {/* AI-Generated Actionable Summary Card */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-cyan-500/30 text-xs leading-relaxed text-slate-300">
              <div className="font-mono text-[10px] text-cyan-400 font-bold uppercase mb-1 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> AI Ensemble Trigger Rationale
              </div>
              Coincident <strong>{telemetry.radarDbz} dBZ Doppler Radar</strong> core (+38% SHAP weight),{" "}
              <strong>{telemetry.awsMmHr} mm/hr AWS gauge</strong> spike, and INSAT-3DS cloud-top cooling (204.5 K) over SCS-CN 94 urban basin exceed storm-drain capacity by 44.6 mm/hr.
            </div>

            {/* Primary CTA Buttons */}
            <button
              onClick={() => setSmsBroadcasted(true)}
              className="w-full py-2.5 px-4 rounded-lg font-mono text-xs font-bold uppercase tracking-wider bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)] transition-all flex items-center justify-center gap-2"
            >
              <Send className="w-4 h-4" />
              {smsBroadcasted
                ? "✓ SMS Alerts Dispatched to Zone A (145,000 Citizens)"
                : "Broadcast SMS Alerts to Zone A"}
            </button>

            <button
              onClick={() => setEvacDeployed(true)}
              className="w-full py-2.5 px-4 rounded-lg font-mono text-xs font-bold uppercase tracking-wider bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400 text-amber-200 transition-all flex items-center justify-center gap-2"
            >
              <Navigation className="w-4 h-4" />
              {evacDeployed
                ? "✓ NDRF Evacuation Route Maps Deployed"
                : "Deploy Evacuation Route Maps"}
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
}
