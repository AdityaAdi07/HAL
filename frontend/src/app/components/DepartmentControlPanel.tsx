"use client";

import React, { useState, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Box, Cylinder, Sphere } from "@react-three/drei";
import * as THREE from "three";
import { useRef } from "react";

// Dept-specific 3D models matching legacy MAT palette
function DeptModel({ dept, isLightMode = false }: { dept: string; isLightMode?: boolean }) {
  const spinRef = useRef<THREE.Group>(null!);
  useFrame(({ clock }) => {
    if (spinRef.current) spinRef.current.rotation.y = clock.getElapsedTime() * 0.8;
  });

  const metalColor = isLightMode ? "#718096" : "#607080";
  const shinyColor = isLightMode ? "#a0aec0" : "#90a0b0";
  const woodColor = isLightMode ? "#975A16" : "#5C3D1E";

  if (dept === "MECHATRONICS") return (
    <group ref={spinRef}>
      <Cylinder args={[0.55, 0.55, 1.2, 16]} position={[0, 0, 0]}>
        <meshStandardMaterial color={metalColor} roughness={0.3} metalness={0.85} />
      </Cylinder>
      <Cylinder args={[0.12, 0.12, 2.2, 8]} position={[0, 0, 0]} rotation={[Math.PI/2, 0, 0]}>
        <meshStandardMaterial color={shinyColor} roughness={0.2} metalness={0.9} />
      </Cylinder>
      {([-1.0, 1.0] as number[]).map((x, i) => (
        <Cylinder key={i} args={[0.3, 0.3, 0.16, 12]} position={[x, 0, 0]}>
          <meshStandardMaterial color={shinyColor} roughness={0.2} metalness={0.9} />
        </Cylinder>
      ))}
    </group>
  );

  if (dept === "FABRICS") return (
    <group ref={spinRef}>
      {/* Warp beam */}
      <Cylinder args={[0.2, 0.2, 3.2, 16]} rotation={[Math.PI/2, 0, 0]}>
        <meshStandardMaterial color={shinyColor} roughness={0.2} metalness={0.9} />
      </Cylinder>
      {/* Side frames */}
      {([-1.5, 1.5] as number[]).map((x, i) => (
        <Box key={i} args={[0.18, 2.2, 0.18]} position={[x, 0, 0]}>
          <meshStandardMaterial color={woodColor} roughness={0.85} metalness={0} />
        </Box>
      ))}
      {/* Reed */}
      <Box args={[3.0, 1.0, 0.08]} position={[0, 0, 0.3]}>
        <meshStandardMaterial color="#8B5E3C" roughness={0.7} metalness={0.1} />
      </Box>
    </group>
  );

  if (dept === "SENSORS") return (
    <group ref={spinRef}>
      <Sphere args={[0.9, 24, 24]}>
        <meshStandardMaterial color={metalColor} roughness={0.35} metalness={0.7} wireframe />
      </Sphere>
      {([0, 1, 2, 3] as number[]).map((i) => (
        <Box key={i}
          args={[0.28, 0.04, 0.36]}
          position={[Math.cos((i / 4) * Math.PI * 2) * 1.3, 0, Math.sin((i / 4) * Math.PI * 2) * 1.3]}
        >
          <meshStandardMaterial color="#1a5c2a" roughness={0.3} metalness={0.4} emissive={isLightMode ? "#0077ff" : "#00e5ff"} emissiveIntensity={0.4} />
        </Box>
      ))}
    </group>
  );

  if (dept === "POWER") return (
    <group ref={spinRef}>
      <Box args={[1.0, 1.8, 0.8]}>
        <meshStandardMaterial color={metalColor} roughness={0.4} metalness={0.7} />
      </Box>
      <Box args={[0.6, 0.4, 0.02]} position={[0, 0.3, 0.41]}>
        <meshStandardMaterial color={isLightMode ? "#2d3748" : "#000a14"} emissive={isLightMode ? "#0077ff" : "#00e5ff"} emissiveIntensity={0.6} />
      </Box>
      {([0, 0.35, 0.7] as number[]).map((y, i) => (
        <Sphere key={i} args={[0.07, 8, 8]} position={[0, -0.5 + y, 0.42]}>
          <meshStandardMaterial
            color={i === 0 ? (isLightMode ? "#16a34a" : "#76ff03") : i === 1 ? (isLightMode ? "#f59e0b" : "#ff9100") : (isLightMode ? "#0077ff" : "#00e5ff")}
            emissive={i === 0 ? (isLightMode ? "#16a34a" : "#76ff03") : i === 1 ? (isLightMode ? "#f59e0b" : "#ff9100") : (isLightMode ? "#0077ff" : "#00e5ff")}
            emissiveIntensity={0.9}
          />
        </Sphere>
      ))}
    </group>
  );

  if (dept === "ASSEMBLY") return (
    <group ref={spinRef}>
      {/* Frame posts */}
      {([[-1.5, 0, -0.9], [1.5, 0, -0.9], [-1.5, 0, 0.9], [1.5, 0, 0.9]] as [number,number,number][]).map(([x,,z], i) => (
        <Box key={i} args={[0.16, 2.2, 0.16]} position={[x, 0, z]}>
          <meshStandardMaterial color={woodColor} roughness={0.85} metalness={0} />
        </Box>
      ))}
      <Box args={[3.2, 0.18, 0.18]} position={[0, 1.05, -0.9]}>
        <meshStandardMaterial color="#8B5E3C" roughness={0.8} metalness={0} />
      </Box>
      <Cylinder args={[0.12, 0.12, 3.5, 12]} rotation={[0, 0, Math.PI/2]} position={[0, 1.1, 0]}>
        <meshStandardMaterial color={shinyColor} roughness={0.15} metalness={0.95} />
      </Cylinder>
      <Sphere args={[0.18, 12, 12]} position={[0, 1.6, 0]}>
        <meshStandardMaterial color={isLightMode ? "#ef4444" : "#ff1744"} emissive={isLightMode ? "#ef4444" : "#ff1744"} emissiveIntensity={0.7} roughness={0.4} metalness={0.2} />
      </Sphere>
    </group>
  );

  return <Box><meshStandardMaterial color={metalColor} roughness={0.5} metalness={0.5} /></Box>;
}

// Data tables per dept
const DEPT_DATA: Record<string, { load: string; capacity: string; wait: string; workers: number; loadColor: string; code: string }> = {
  MECHATRONICS: { code: "DEPT-MECH", load: "85%", capacity: "100%", wait: "2 min",  workers: 8,  loadColor: "#00e5ff" },
  FABRICS:      { code: "DEPT-FAB",  load: "92%", capacity: "100%", wait: "5 min",  workers: 12, loadColor: "#00e5ff" },
  SENSORS:      { code: "DEPT-SENS", load: "40%", capacity: "100%", wait: "0 min",  workers: 6,  loadColor: "#ff9100" },
  POWER:        { code: "DEPT-PWR",  load: "75%", capacity: "100%", wait: "1 min",  workers: 7,  loadColor: "#00e5ff" },
  ASSEMBLY:     { code: "DEPT-ASSY", load: "98%", capacity: "100%", wait: "14 min", workers: 18, loadColor: "#ff1744" },
};

// Catalog components per dept
const DEPT_COMPONENTS: Record<string, Array<{ code: string; name: string; pct: number; status: string; statusType: "ok" | "warn" | "fault" }>> = {
  MECHATRONICS: [
    { code: "MECH-MOTOR",    name: "Drive motor assembly",           pct: 82,  status: "IN PROGRESS", statusType: "ok" },
    { code: "MECH-DRIVER",   name: "Motor driver/controller unit",   pct: 100, status: "COMPLETED",   statusType: "ok" },
    { code: "MECH-COUPLING", name: "Coupling & mount bracket",        pct: 45,  status: "IN PROGRESS", statusType: "ok" },
    { code: "MECH-CHAIN",    name: "Chain drive assembly",           pct: 60,  status: "IN PROGRESS", statusType: "ok" },
    { code: "MECH-TENSIONER",name: "Chain tensioner unit",           pct: 0,   status: "QUEUED",      statusType: "warn" },
  ],
  FABRICS: [
    { code: "FAB-WARP-BEAM", name: "Warp beam core & flanges",        pct: 90,  status: "IN PROGRESS", statusType: "ok" },
    { code: "FAB-HEALD",     name: "Heald wire & shaft frame",       pct: 100, status: "COMPLETED",   statusType: "ok" },
    { code: "FAB-REED",      name: "Reed comb & sley cap",           pct: 75,  status: "IN PROGRESS", statusType: "ok" },
    { code: "FAB-SHUTTLE",   name: "Shuttle box & picker assembly",  pct: 85,  status: "IN PROGRESS", statusType: "ok" },
    { code: "FAB-TEMPLE",    name: "Temple cylinder & grip ring",    pct: 50,  status: "IN PROGRESS", statusType: "ok" },
  ],
  SENSORS: [
    { code: "SENS-TENSION",  name: "Yarn tension load cell",         pct: 40,  status: "STARVED",     statusType: "warn" },
    { code: "SENS-OPTICAL",  name: "Weft break optical detector",    pct: 35,  status: "UNDERLOAD",   statusType: "warn" },
    { code: "SENS-ENCODER",  name: "Loom shaft rotary encoder",      pct: 45,  status: "UNDERLOAD",   statusType: "warn" },
    { code: "SENS-TEMP",     name: "Bearing thermal probe set",      pct: 100, status: "COMPLETED",   statusType: "ok" },
  ],
  POWER: [
    { code: "PWR-SUPPLY",    name: "24V/15A industrial PSU",         pct: 80,  status: "IN PROGRESS", statusType: "ok" },
    { code: "PWR-DIST",      name: "Power distribution board",       pct: 100, status: "COMPLETED",   statusType: "ok" },
    { code: "PWR-ESTOP",     name: "Emergency stop circuit & relay", pct: 100, status: "COMPLETED",   statusType: "ok" },
    { code: "PWR-HARNESS",   name: "Main machine wiring harness",    pct: 70,  status: "IN PROGRESS", statusType: "ok" },
  ],
  ASSEMBLY: [
    { code: "ASY-FRAME",     name: "Loom main chassis & legs",       pct: 98,  status: "BOTTLENECK",  statusType: "fault" },
    { code: "ASY-MECH-INST", name: "Mechatronics mounting",          pct: 95,  status: "BOTTLENECK",  statusType: "fault" },
    { code: "ASY-FAB-INST",  name: "Warp beam & shed install",       pct: 92,  status: "BOTTLENECK",  statusType: "fault" },
    { code: "ASY-CALIB",     name: "Tension & stroke calibration",   pct: 15,  status: "WAITING",     statusType: "warn" },
    { code: "ASY-QA",        name: "24-hr continuous run test & QA", pct: 0,   status: "QUEUED",      statusType: "warn" },
  ],
};

export default function DepartmentControlPanel({
  dept,
  onClose,
  isLightMode: propLightMode = false,
  onToggleTheme,
}: {
  dept: string;
  onClose: () => void;
  isLightMode?: boolean;
  onToggleTheme?: () => void;
}) {
  const [internalLightMode, setInternalLightMode] = useState(propLightMode);
  const [isRebalanced, setIsRebalanced] = useState(false);

  useEffect(() => {
    if (typeof document !== "undefined") {
      const isBodyLight = document.body.classList.contains("light-mode");
      setInternalLightMode(isBodyLight || propLightMode);
    }
  }, [propLightMode]);

  const [chatInput, setChatInput] = useState("");
  const [chatLog, setChatLog] = useState([
    { role: "system", content: "Department intelligence agent connected. Ready to analyze component loads." },
  ]);
  const [logs, setLogs] = useState<Array<{ text: string; type: "muted" | "ok" | "fault" | "warn" }>>([
    { text: `${new Date().toLocaleTimeString()} > Initializing ${dept} telemetry...`, type: "muted" },
    { text: `${new Date().toLocaleTimeString()} > MQTT broker synced with digital twin.`, type: "ok" },
    { text: `${new Date().toLocaleTimeString()} > Processing BOM components batch #BOM-9102...`, type: "muted" },
    {
      text: dept === "ASSEMBLY"
        ? `${new Date().toLocaleTimeString()} > ALERT: Queue threshold exceeded! Downstream choked.`
        : `${new Date().toLocaleTimeString()} > Cycle time within ±3% standard deviation.`,
      type: dept === "ASSEMBLY" ? "fault" : "ok",
    },
  ]);

  const [isTyping, setIsTyping] = useState(false);
  const isOverload = dept === "ASSEMBLY" && !isRebalanced;
  const data = DEPT_DATA[dept] ?? DEPT_DATA["MECHATRONICS"];
  const components = DEPT_COMPONENTS[dept] ?? DEPT_COMPONENTS["MECHATRONICS"];

  const handleToggle = () => {
    const next = !internalLightMode;
    setInternalLightMode(next);
    if (typeof document !== "undefined") {
      if (next) {
        document.body.classList.add("light-mode");
        localStorage.setItem("hal-theme", "light");
      } else {
        document.body.classList.remove("light-mode");
        localStorage.setItem("hal-theme", "dark");
      }
    }
    if (onToggleTheme) {
      onToggleTheme();
    }
  };

  const handleExecuteShift = () => {
    setIsRebalanced(true);
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [
      ...prev,
      { text: `${time} > ACTION EXECUTED: Rebalanced 2 operators from FABRICS -> SENSORS/ASSY.`, type: "ok" },
      { text: `${time} > Line status upgraded to NOMINAL. Throughput projected at 6.8 looms/day.`, type: "ok" },
    ]);
    setChatLog((prev) => [
      ...prev,
      {
        role: "assistant",
        content: `[REBALANCING COMPLETE] Transferred 2 workers from FABRICS to unblock starved component buffers. Assembly load reduced from 98% to 82% (Nominal).`,
      },
    ]);
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatLog((prev) => [...prev, { role: "user", content: userMsg }]);
    setChatInput("");
    setIsTyping(true);
    setTimeout(() => {
      let reply = `[${dept}] Current load is ${isRebalanced ? "82%" : data.load} with ${data.workers + (isRebalanced ? 2 : 0)} active operators.`;
      if (isRebalanced) {
        reply += " Workforce rebalanced. All workstations operating stably without bottlenecks.";
      } else if (isOverload) {
        reply += " Critical assembly backlog identified. Recommended action: click 'EXECUTE WORKER TRANSFER' to loan 2 operators from FABRICS.";
      } else {
        reply += " All active component pipelines operating within nominal tolerances.";
      }
      setChatLog((prev) => [...prev, { role: "assistant", content: reply }]);
      setIsTyping(false);
    }, 1100);
  };

  // Coordinated theme colors
  const accent = internalLightMode ? "#0077ff" : "#00e5ff";
  const accentGreen = internalLightMode ? "#16a34a" : "#76ff03";
  const accentWarn = internalLightMode ? "#f59e0b" : "#ff9100";
  const accentFault = internalLightMode ? "#ef4444" : "#ff1744";
  const textPrimary = internalLightMode ? "#1a202c" : "#e0e8f0";
  const textMuted = internalLightMode ? "#64748b" : "#4a5568";

  return (
    <div className="dept-modal">
      {/* HEADER */}
      <div className="dept-modal-header">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className="dept-modal-title">
            {dept} <span style={{ color: textMuted, fontSize: 12, fontWeight: "normal" }}>// COMPONENT INTELLIGENCE &amp; OPTIMIZATION</span>
          </div>
          <span
            className={isOverload ? "dept-badge-bottleneck" : "dept-badge-nominal"}
            style={{
              fontSize: 9,
              padding: "2px 8px",
              borderRadius: 12,
              fontWeight: "bold",
            }}
          >
            {isOverload ? "CRITICAL BOTTLENECK" : isRebalanced ? "REBALANCED & NOMINAL" : "OPERATIONAL NOMINAL"}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button
            onClick={handleToggle}
            className="theme-btn"
            id="modal-theme-toggle-btn"
            title={internalLightMode ? "Switch to Dark Mode" : "Switch to Light Mode"}
            aria-label="Toggle theme"
          >
            {internalLightMode ? "🌙" : "☀️"}
          </button>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: `1px solid ${accent}`,
              color: accent,
              padding: "6px 18px",
              borderRadius: 4,
              cursor: "pointer",
              fontFamily: "inherit",
              fontSize: 10,
              letterSpacing: 2,
              fontWeight: "bold",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = internalLightMode ? "rgba(0,119,255,0.1)" : "rgba(0,229,255,0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            BACK TO TWIN
          </button>
        </div>
      </div>

      {/* GRID */}
      <div style={{ display: "flex", flex: 1, gap: 16, overflow: "hidden" }}>

        {/* LEFT COLUMN: Stats, Components Board, Predictions */}
        <div style={{ flex: "0 0 46%", display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" }}>
          
          {/* Stats Card */}
          <div className="dept-modal-card">
            <div className="dept-card-title">Current Telemetry</div>
            <div style={{ display: "flex", justifyContent: "space-around", textAlign: "center" }}>
              {[
                { label: "LOAD", val: isRebalanced ? "82%" : data.load, color: isOverload ? accentFault : isRebalanced ? accentGreen : data.load === "40%" ? accentWarn : accent },
                { label: "CAPACITY", val: data.capacity, color: accent },
                { label: "WAIT TIME", val: isRebalanced ? "3 min" : data.wait, color: isOverload ? accentWarn : accentGreen },
                { label: "OPERATORS", val: `${data.workers + (isRebalanced ? 2 : 0)}`, color: textPrimary },
              ].map((s) => (
                <div key={s.label}>
                  <div style={{ fontSize: 22, color: s.color, fontWeight: "bold" }}>{s.val}</div>
                  <div style={{ fontSize: 9, color: textMuted, marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Components Board */}
          <div className="dept-modal-card">
            <div className="dept-card-title">
              <span>Active Components In Production</span>
              <span style={{ fontSize: 9, color: textMuted, textTransform: "none" }}>{components.length} Bill of Materials units</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {components.map((c) => {
                const isItemResolved = isRebalanced && c.statusType === "fault";
                const displayStatus = isItemResolved ? "IN PROGRESS" : c.status;
                const displayType = isItemResolved ? "ok" : c.statusType;
                const statusColor = displayType === "fault" ? accentFault : displayType === "warn" ? accentWarn : accentGreen;
                
                return (
                  <div key={c.code} className="dept-row-item" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                    <div style={{ minWidth: 110 }}>
                      <div style={{ fontSize: 10, color: accent, fontWeight: "bold" }}>{c.code}</div>
                      <div style={{ fontSize: 9, color: textMuted }}>{c.name}</div>
                    </div>
                    <div style={{ flex: 1, margin: "0 8px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, marginBottom: 3 }}>
                        <span style={{ color: textMuted }}>Progress</span>
                        <span style={{ fontWeight: "bold", color: statusColor }}>{c.pct}%</span>
                      </div>
                      <div style={{ height: 5, background: internalLightMode ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.08)", borderRadius: 3, overflow: "hidden" }}>
                        <div
                          style={{
                            height: "100%",
                            width: `${c.pct}%`,
                            background: statusColor,
                          }}
                        />
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: 8,
                        padding: "2px 6px",
                        borderRadius: 3,
                        fontWeight: "bold",
                        color: statusColor,
                        border: `1px solid ${statusColor}`,
                      }}
                    >
                      {displayStatus}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Predictions & Load Balancing */}
          <div className="dept-modal-card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div className="dept-card-title">Predictions &amp; Balancing</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
              <div className="dept-row-item" style={{ borderLeft: `3px solid ${isOverload ? accentFault : accentGreen}` }}>
                <div style={{ fontSize: 9, color: textMuted }}>LOAD PREDICTION (1HR HORIZON)</div>
                <div style={{ fontSize: 11, marginTop: 3, color: textPrimary }}>
                  {isOverload
                    ? "Queue exceeds capacity by 20%. Downstream line starved."
                    : "Stable throughput. Workstation utilization within optimal bounds."}
                </div>
              </div>
              <div className="dept-row-item" style={{ borderLeft: `3px solid ${accentGreen}` }}>
                <div style={{ fontSize: 9, color: textMuted }}>RESOURCE HEALTH</div>
                <div style={{ fontSize: 11, marginTop: 3, color: textPrimary }}>
                  Tooling &amp; wear metrics green. 0 maintenance actions required for next 6 hours.
                </div>
              </div>
              <div className="dept-row-item" style={{ borderLeft: `3px solid ${isOverload ? accentWarn : accentGreen}` }}>
                <div style={{ fontSize: 9, color: textMuted }}>RECOMMENDED REBALANCING</div>
                <div style={{ fontSize: 11, marginTop: 3, color: textPrimary }}>
                  {isOverload
                    ? "Shift 2 operators from FABRICS to clear queue and eliminate choke point."
                    : "Workforce rebalanced. Nominal throughput on target."}
                </div>
                {isOverload && (
                  <button
                    onClick={handleExecuteShift}
                    style={{
                      marginTop: 8,
                      background: accentWarn,
                      color: internalLightMode ? "#ffffff" : "#000000",
                      border: "none",
                      padding: "6px 14px",
                      fontSize: 10,
                      fontWeight: "bold",
                      cursor: "pointer",
                      borderRadius: 3,
                      fontFamily: "inherit",
                      letterSpacing: 1,
                    }}
                  >
                    EXECUTE WORKER TRANSFER
                  </button>
                )}
                {isRebalanced && (
                  <div style={{ marginTop: 6, fontSize: 10, color: accentGreen, fontWeight: "bold" }}>
                    ✓ 2 Workers Loaned from FABRICS. Bottleneck Cleared.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: 3D Twin View, Event Log & Chat */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
          
          {/* 3D Component Twin View */}
          <div className="dept-modal-card" style={{ flex: "0 0 52%", padding: 0 }}>
            <div
              style={{
                position: "absolute",
                top: 10,
                left: 10,
                zIndex: 10,
                background: internalLightMode ? "#ffffff" : "#111418",
                border: `1px solid ${accent}`,
                color: accent,
                padding: "4px 10px",
                fontSize: 10,
                fontWeight: "bold",
                letterSpacing: 1,
                borderRadius: 4,
                boxShadow: internalLightMode ? "0 2px 6px rgba(0,0,0,0.06)" : undefined,
              }}
            >
              LIVE 3D COMPONENT TWIN
            </div>
            <Canvas
              camera={{ position: [0, 1.5, 5.5], fov: 45 }}
              style={{ borderRadius: 8, background: internalLightMode ? "#f1f5f9" : "#0a0c0f", transition: "background 0.3s" }}
            >
              <ambientLight color={internalLightMode ? 0xffffff : 0x1a2030} intensity={internalLightMode ? 1.4 : 0.8} />
              <directionalLight color="#ffffff" intensity={internalLightMode ? 1.2 : 0.6} position={[4, 6, 4]} />
              <pointLight color={accent} intensity={2.0} position={[3, 3, 3]} />
              <pointLight color={accentGreen} intensity={0.5} position={[-3, 2, -2]} />
              <DeptModel dept={dept} isLightMode={internalLightMode} />
              <OrbitControls autoRotate autoRotateSpeed={1.5} enableZoom={false} minPolarAngle={0.3} maxPolarAngle={Math.PI / 2} />
            </Canvas>
          </div>

          {/* Bottom Row: Event Log + Context LLM Agent */}
          <div style={{ flex: 1, display: "flex", gap: 12, minHeight: 0 }}>
            
            {/* Event Log Terminal */}
            <div className="dept-modal-card" style={{ flex: "0 0 44%", display: "flex", flexDirection: "column", minHeight: 0 }}>
              <div className="dept-card-title">Event Log Terminal</div>
              <div style={{ fontSize: 9, display: "flex", flexDirection: "column", gap: 4, overflowY: "auto", flex: 1 }}>
                {logs.map((l, i) => (
                  <div
                    key={i}
                    style={{
                      color:
                        l.type === "ok"
                          ? accentGreen
                          : l.type === "fault"
                          ? accentFault
                          : l.type === "warn"
                          ? accentWarn
                          : textMuted,
                      fontWeight: l.type === "fault" || l.type === "ok" ? "bold" : "normal",
                    }}
                  >
                    {l.text}
                  </div>
                ))}
              </div>
            </div>

            {/* Context LLM Agent */}
            <div className="dept-modal-card" style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
              <div className="dept-card-title">Department Copilot</div>
              <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6, marginBottom: 8 }}>
                {chatLog.map((msg, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "6px 8px",
                      borderRadius: 4,
                      fontSize: 10,
                      lineHeight: 1.4,
                      maxWidth: "92%",
                      background: msg.role === "user" ? (internalLightMode ? "rgba(0,119,255,0.08)" : "rgba(0,229,255,0.08)") : msg.role === "system" ? "transparent" : (internalLightMode ? "#f8fafc" : "rgba(255,255,255,0.04)"),
                      borderLeft: msg.role === "user" ? `3px solid ${accent}` : msg.role === "system" ? `3px solid ${textMuted}` : `3px solid ${accentGreen}`,
                      alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                      color: msg.role === "system" ? textMuted : textPrimary,
                      borderTop: internalLightMode && msg.role !== "system" ? "1px solid #e2e8f0" : undefined,
                      borderRight: internalLightMode && msg.role !== "system" ? "1px solid #e2e8f0" : undefined,
                      borderBottom: internalLightMode && msg.role !== "system" ? "1px solid #e2e8f0" : undefined,
                    }}
                  >
                    {msg.content}
                  </div>
                ))}
                {isTyping && <div style={{ color: textMuted, fontSize: 9, fontStyle: "italic" }}>Copilot is calculating...</div>}
              </div>
              <form onSubmit={handleChatSubmit} style={{ display: "flex", gap: 6 }}>
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder={`Ask about ${dept} status...`}
                  className="dept-chat-input"
                  style={{ flex: 1 }}
                />
                <button
                  type="submit"
                  style={{
                    background: accent,
                    color: internalLightMode ? "#ffffff" : "#000000",
                    border: "none",
                    padding: "0 12px",
                    borderRadius: 4,
                    fontWeight: "bold",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    fontSize: 11,
                  }}
                >
                  &gt;
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
