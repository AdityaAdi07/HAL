"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import "./globals.css";
import DepartmentControlPanel from "./components/DepartmentControlPanel";

const Factory3D = dynamic(() => import("./components/Factory3D"), { ssr: false });

export default function TwinDashboard() {
  const [activeDept, setActiveDept] = useState<string | null>(null);
  const [timeStr, setTimeStr] = useState("--:--:--");
  const [isLightMode, setIsLightMode] = useState(false);

  const [simulated, setSimulated] = useState(false);

  const capacity = { mech: 85, fab: simulated ? 84 : 92, sens: simulated ? 78 : 40, pwr: 75, assy: simulated ? 82 : 98 };

  useEffect(() => {
    const t = setInterval(() => setTimeStr(new Date().toLocaleTimeString()), 1000);
    const saved = localStorage.getItem("hal-theme");
    if (saved === "light") {
      setIsLightMode(true);
      document.body.classList.add("light-mode");
    }
    return () => clearInterval(t);
  }, []);

  const toggleTheme = () => {
    setIsLightMode((prev) => {
      const next = !prev;
      if (next) {
        document.body.classList.add("light-mode");
        localStorage.setItem("hal-theme", "light");
      } else {
        document.body.classList.remove("light-mode");
        localStorage.setItem("hal-theme", "dark");
      }
      return next;
    });
  };

  const getStatus = (val: number) => val < 70 ? "underload" : val > 95 ? "overload" : "healthy";
  const fmtStatus = (val: number) => val < 70 ? "UNDERLOAD" : val > 95 ? "OVERLOAD" : "HEALTHY";
  const gaugeColor = (val: number) => val > 95 ? "var(--fault)" : val < 70 ? "var(--warn)" : "var(--accent)";

  const DEPTS = [
    { label: "MECH",    val: capacity.mech },
    { label: "FABRICS", val: capacity.fab  },
    { label: "SENSORS", val: capacity.sens },
    { label: "POWER",   val: capacity.pwr  },
  ];

  return (
    <div className="layout-container">
      <header className="topbar">
        <div className="logo">Powerloom <span>//</span> Digital Twin</div>
        <div className="status-pill">
          <div className="status-dot healthy" />
          <span>SYSTEM LIVE</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            className="theme-btn"
            id="theme-toggle-btn"
            onClick={toggleTheme}
            title={isLightMode ? "Switch to Dark Mode" : "Switch to Light Mode"}
            aria-label="Toggle theme"
          >
            {isLightMode ? "🌙" : "☀️"}
          </button>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--muted)", letterSpacing: 1 }}>{timeStr}</span>
        </div>
      </header>

      {/* LEFT PANEL */}
      <aside className="side-panel fade-in">
        <div className="glass-panel">
          <div className="card-title">Factory Overview</div>
          <div className="metric-group">
            <div className="big-metric">
              <span className="big-num" style={{ fontSize: 28, color: "var(--accent)" }}>5.9</span>
              <span className="big-label">Looms / Day</span>
            </div>
            <div className="big-metric">
              <span className="big-num" style={{ fontSize: 28, color: "var(--accent2)" }}>98%</span>
              <span className="big-label">Yield</span>
            </div>
          </div>
          <div className="gauge-container">
            <div className="gauge-header">
              <span>Overall Schedule</span>
              <span className="gauge-value">84%</span>
            </div>
            <div className="gauge-track"><div className="gauge-fill" style={{ width: "84%" }} /></div>
          </div>
        </div>

        <div className="glass-panel">
          <div className="card-title">Department Status</div>
          <div className="dept-grid">
            {DEPTS.map((d) => (
              <div key={d.label} className="dept-card" onClick={() => setActiveDept(d.label)}>
                <span className="dept-card-header">{d.label}</span>
                <span className={`dept-status ${getStatus(d.val)}`}>{fmtStatus(d.val)}</span>
                <div className="gauge-track" style={{ marginTop: 2 }}>
                  <div className="gauge-fill" style={{ width: `${d.val}%`, background: gaugeColor(d.val), boxShadow: `0 0 8px ${gaugeColor(d.val)}` }} />
                </div>
              </div>
            ))}
            <div className="dept-card" style={{ gridColumn: "span 2", borderColor: "rgba(255,23,68,0.35)", background: "rgba(255,23,68,0.04)" }} onClick={() => setActiveDept("ASSEMBLY")}>
              <span className="dept-card-header" style={{ color: "var(--fault)" }}>ASSEMBLY</span>
              <span className={`dept-status ${getStatus(capacity.assy)}`}>{fmtStatus(capacity.assy)} — BOTTLENECK</span>
              <div className="gauge-track" style={{ marginTop: 2, height: 8 }}>
                <div className="gauge-fill" style={{ width: `${capacity.assy}%`, background: "var(--fault)", boxShadow: "0 0 8px var(--fault)" }} />
              </div>
            </div>
          </div>
        </div>

        <div className="glass-panel">
          <div className="card-title">Active Orders</div>
          {[{ id: "ORD-0041", model: "LM-200", pct: 72, color: "var(--accent)" }, { id: "ORD-0042", model: "LM-100", pct: 45, color: "var(--accent2)" }, { id: "ORD-0043", model: "LM-300", pct: 18, color: "var(--warn)" }].map((o) => (
            <div key={o.id} style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 10, marginBottom: 4 }}>
                <span style={{ color: "var(--accent)" }}>{o.id}</span>
                <span style={{ color: "var(--muted)" }}>{o.model}</span>
                <span style={{ color: o.color, fontWeight: "bold" }}>{o.pct}%</span>
              </div>
              <div className="gauge-track"><div className="gauge-fill" style={{ width: `${o.pct}%`, background: o.color, boxShadow: `0 0 8px ${o.color}` }} /></div>
            </div>
          ))}
        </div>
      </aside>

      {/* CENTER VIEWPORT */}
      <main className="viewport" style={{ position: "relative" }}>
        <Factory3D onPodClick={setActiveDept} isLightMode={isLightMode} />
        {activeDept && (
          <DepartmentControlPanel
            dept={activeDept}
            onClose={() => setActiveDept(null)}
            isLightMode={isLightMode}
            onToggleTheme={toggleTheme}
          />
        )}
        <div className="controls-hint">DRAG to rotate  ·  SCROLL to zoom  ·  RIGHT-DRAG to pan</div>
      </main>

      {/* RIGHT PANEL */}
      <aside className="side-panel fade-in" style={{ animationDelay: "0.2s" }}>
        <div className="glass-panel" style={{ borderColor: simulated ? "rgba(118,255,3,0.3)" : "rgba(255,23,68,0.25)" }}>
          <div className="card-title" style={{ color: simulated ? "var(--accent2)" : "var(--fault)" }}>
            {simulated ? "Root Cause Resolved" : "Active Root Cause"}
          </div>
          <div style={{ color: simulated ? "var(--accent2)" : "var(--fault)", fontFamily: "var(--font-mono)", fontWeight: "bold", marginBottom: 6, fontSize: 11 }}>
            {simulated ? "Assembly → BALANCED (82% Load)" : "Assembly → OVERLOADED"}
          </div>
          <div style={{ color: "var(--muted)", fontSize: 10, marginBottom: 10, lineHeight: 1.6 }}>
            {simulated
              ? "Reallocated 2 workers FABRICS → SENSORS. Feed buffer restored, clearing bottleneck."
              : "Queue in ASSY-01 exceeds 45 min. Root: SENSORS starved at 40% load."}
          </div>
          <div style={{ background: simulated ? "rgba(118,255,3,0.06)" : "rgba(255,23,68,0.06)", border: `1px solid ${simulated ? "rgba(118,255,3,0.2)" : "rgba(255,23,68,0.2)"}`, borderRadius: 6, padding: "8px 10px", fontSize: 10, marginBottom: 12 }}>
            <div style={{ color: "var(--warn)", fontFamily: "var(--font-mono)", marginBottom: 4 }}>
              CONFIDENCE: {simulated ? "98%" : "91%"}
            </div>
            <div style={{ color: "var(--text)" }}>
              {simulated ? "✓ 2 Workers loaned. Throughput optimal at 6.8 looms/day." : "Loan 2 workers FABRICS → SENSORS to unblock upstream."}
            </div>
          </div>
          <button
            className="req-btn solid"
            style={{
              width: "100%",
              padding: 10,
              fontSize: 10,
              background: simulated ? "var(--accent2)" : undefined,
              color: simulated ? "#000" : undefined,
            }}
            onClick={() => setSimulated((prev) => !prev)}
          >
            {simulated ? "✓ SOLUTION ACTIVE — RESET" : "▶ SIMULATE SOLUTION"}
          </button>
        </div>

        <div className="glass-panel">
          <div className="card-title">Predictions (7-day)</div>
          {[
            { label: "On-Time Probability", val: simulated ? "94%" : "73%", st: simulated ? "ok" : "warn" },
            { label: "Avg Build Time (LM-100)", val: simulated ? "3.6 days" : "4.2 days", st: "ok" },
            { label: "ASSY Bottleneck Risk", val: simulated ? "P90: LOW" : "P90: HIGH", st: simulated ? "ok" : "fault" },
            { label: "Predicted Cap (MECH)", val: "88%", st: "ok" },
          ].map((p) => (
            <div key={p.label} className="kv-row">
              <span className="kv-key">{p.label}</span>
              <span className={`kv-value ${p.st}`}>{p.val}</span>
            </div>
          ))}
        </div>

        <div className="glass-panel">
          <div className="card-title">Current Shift (S1)</div>
          {[
            { dept: "MECH", w: 8 },
            { dept: "FABRICS", w: simulated ? 10 : 12 },
            { dept: "SENSORS", w: simulated ? 8 : 6 },
            { dept: "POWER", w: 7 },
            { dept: "ASSY", w: 18 },
          ].map((s) => (
            <div key={s.dept} className="kv-row">
              <span className="kv-key">{s.dept}</span>
              <span className="kv-value ok">{s.w} workers</span>
            </div>
          ))}
        </div>
      </aside>

      {/* BOTTOM BAR */}
      <div className="bottombar">
        <div className="bstat">STATUS <span>LIVE</span></div>
        <div className="bstat">LOOMS/DAY <span>{simulated ? "6.8" : "5.9"}</span></div>
        <div className="bstat">
          BOTTLENECK{" "}
          <span style={{ color: simulated ? "var(--accent2)" : "var(--fault)" }}>
            {simulated ? "NONE" : "ASSY"}
          </span>
        </div>
        <div className="bstat">SHIFT <span>S1 · 06:00 — 14:00</span></div>
        <div style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--muted)" }}>SYNTHETIC DATA · HAL v0.1</div>
      </div>
    </div>
  );
}
