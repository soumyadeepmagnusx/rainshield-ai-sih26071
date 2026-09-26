import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "RAINSHIELD-AI v6.0 | MoES SIH26071 Flood & Heavy Rainfall Early Warning Command Center",
  description:
    "AI/ML-Based Integrated Heavy Rainfall Early Warning and 2D Inundation Prediction System using INSAT-3DS Satellite, IMD Doppler Radar, AWS, and NCMRWF 1km NWP (Team BWU INCURSION 1.0).",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-50 antialiased selection:bg-cyan-500/30">
        {children}
      </body>
    </html>
  );
}
