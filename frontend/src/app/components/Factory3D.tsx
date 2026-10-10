"use client";

import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Text, Grid } from "@react-three/drei";
import * as THREE from "three";
import { useState } from "react";

// Legacy material palette (matches index.html MAT)
const C = {
  metal:      "#607080",
  metalShiny: "#90a0b0",
  wood:       "#8B5E3C",
  woodDark:   "#5C3D1E",
  accent:     "#00e5ff",
  accent2:    "#76ff03",
  warn:       "#ff9100",
  fault:      "#ff1744",
};

const DEPT_DEFS = [
  { name: "MECHATRONICS", pos: [-7,  0, -5] as [number,number,number], color: "#00e5ff", emissive: "#003344" },
  { name: "FABRICS",      pos: [ 7,  0, -5] as [number,number,number], color: "#00e5ff", emissive: "#002233" },
  { name: "SENSORS",      pos: [-7,  0,  5] as [number,number,number], color: "#ff9100", emissive: "#331500" },
  { name: "POWER",        pos: [ 7,  0,  5] as [number,number,number], color: "#00e5ff", emissive: "#001133" },
  { name: "ASSEMBLY",     pos: [ 0,  0,  0] as [number,number,number], color: "#ff1744", emissive: "#330011" },
];

function DepartmentPod({ position, color, emissive, name, onClick }: {
  position: [number,number,number]; color: string; emissive: string; name: string; onClick: (n: string) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const lightRef = useRef<THREE.PointLight>(null!);

  useFrame(({ clock }) => {
    if (lightRef.current) {
      lightRef.current.intensity = hovered
        ? 3.0 + Math.sin(clock.getElapsedTime() * 4) * 0.6
        : 1.0 + Math.sin(clock.getElapsedTime() * 1.5) * 0.3;
    }
  });

  return (
    <group
      position={position}
      onClick={(e) => { e.stopPropagation(); onClick(name); }}
      onPointerOver={() => { setHovered(true); document.body.style.cursor = "pointer"; }}
      onPointerOut={() => { setHovered(false); document.body.style.cursor = "auto"; }}
    >
      {/* Platform */}
      <mesh position={[0, 0.1, 0]} receiveShadow>
        <boxGeometry args={[5, 0.2, 5]} />
        <meshStandardMaterial color={color} transparent opacity={hovered ? 0.5 : 0.3} roughness={0.4} metalness={0.6} emissive={color} emissiveIntensity={hovered ? 0.4 : 0.12} />
      </mesh>

      {/* Machines */}
      {name === "MECHATRONICS" && <MechMachines hovered={hovered} />}
      {name === "FABRICS"      && <FabricsMachines />}
      {name === "SENSORS"      && <SensorsMachines hovered={hovered} />}
      {name === "POWER"        && <PowerMachines />}
      {name === "ASSEMBLY"     && <AssemblyMachines />}

      {/* Label */}
      <Text position={[0, 3.2, 0]} fontSize={0.38} color={color} anchorX="center" anchorY="middle" outlineWidth={0.025} outlineColor="#000000">
        {name}
      </Text>

      {/* Status light pulse */}
      <pointLight ref={lightRef} color={color} intensity={1.0} distance={8} position={[0, 2.5, 0]} />
    </group>
  );
}

function MechMachines({ hovered }: { hovered: boolean }) {
  const motorRef = useRef<THREE.Mesh>(null!);
  useFrame(({ clock }) => { if (motorRef.current) motorRef.current.rotation.y = clock.getElapsedTime() * 2; });
  return (
    <group>
      <mesh ref={motorRef} position={[0, 0.9, 0]} castShadow>
        <cylinderGeometry args={[0.6, 0.6, 1.4, 16]} />
        <meshStandardMaterial color={C.metalShiny} roughness={0.3} metalness={0.8} />
      </mesh>
      <mesh position={[0, 0.9, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.12, 2.4, 8]} />
        <meshStandardMaterial color={C.metal} roughness={0.4} metalness={0.8} />
      </mesh>
      {([-1.2, 1.2] as number[]).map((x, i) => (
        <mesh key={i} position={[x, 0.9, 0]} castShadow>
          <cylinderGeometry args={[0.32, 0.32, 0.18, 12]} />
          <meshStandardMaterial color={C.metalShiny} roughness={0.2} metalness={0.9} />
        </mesh>
      ))}
      {/* Control box */}
      <mesh position={[1.7, 0.7, 1.5]} castShadow>
        <boxGeometry args={[0.7, 1.0, 0.45]} />
        <meshStandardMaterial color={C.metal} roughness={0.4} metalness={0.7} />
      </mesh>
      <mesh position={[1.7, 0.85, 1.73]}>
        <boxGeometry args={[0.45, 0.28, 0.02]} />
        <meshStandardMaterial color="#001122" emissive="#00e5ff" emissiveIntensity={hovered ? 0.9 : 0.4} />
      </mesh>
    </group>
  );
}

function FabricsMachines() {
  return (
    <group>
      {([-1.6, 1.6] as number[]).map((x, i) => (
        <group key={i} position={[x, 0, 0]}>
          <mesh position={[0, 1.2, 0]} castShadow><boxGeometry args={[0.18, 2.4, 0.18]} /><meshStandardMaterial color={C.woodDark} roughness={0.85} /></mesh>
          <mesh position={[0, 1.2, 1.6]} castShadow><boxGeometry args={[0.18, 2.4, 0.18]} /><meshStandardMaterial color={C.woodDark} roughness={0.85} /></mesh>
        </group>
      ))}
      <mesh position={[0, 0.55, 1.5]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.18, 0.18, 3.2, 16]} />
        <meshStandardMaterial color={C.metalShiny} roughness={0.2} metalness={0.9} />
      </mesh>
      <mesh position={[0, 0.5, 0.2]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.14, 0.14, 3.2, 16]} />
        <meshStandardMaterial color={C.metalShiny} roughness={0.2} metalness={0.9} />
      </mesh>
      <mesh position={[0, 1.5, 0.8]} castShadow>
        <boxGeometry args={[3.0, 0.08, 0.06]} />
        <meshStandardMaterial color="#4488aa" roughness={0.4} metalness={0.6} />
      </mesh>
      <mesh position={[0, 2.3, 0]} castShadow>
        <boxGeometry args={[3.5, 0.2, 0.2]} />
        <meshStandardMaterial color={C.wood} roughness={0.8} />
      </mesh>
    </group>
  );
}

function SensorsMachines({ hovered }: { hovered: boolean }) {
  const boardRef = useRef<THREE.Group>(null!);
  useFrame(({ clock }) => { if (boardRef.current) boardRef.current.rotation.y = clock.getElapsedTime() * 0.9; });
  return (
    <group>
      <mesh position={[0, 0.6, 0]} castShadow>
        <boxGeometry args={[1.4, 0.9, 1.0]} />
        <meshStandardMaterial color={C.metal} roughness={0.4} metalness={0.7} />
      </mesh>
      <mesh position={[0, 0.65, 0.51]}>
        <boxGeometry args={[0.9, 0.55, 0.02]} />
        <meshStandardMaterial color="#001122" emissive="#ff9100" emissiveIntensity={hovered ? 0.9 : 0.35} />
      </mesh>
      <group ref={boardRef} position={[0, 1.5, 0]}>
        {([0, 1, 2, 3] as number[]).map((i) => (
          <mesh key={i} position={[Math.cos((i / 4) * Math.PI * 2) * 0.9, 0, Math.sin((i / 4) * Math.PI * 2) * 0.9]} castShadow>
            <boxGeometry args={[0.3, 0.04, 0.4]} />
            <meshStandardMaterial color="#1a5c2a" roughness={0.3} metalness={0.4} emissive="#00e5ff" emissiveIntensity={hovered ? 0.6 : 0.12} />
          </mesh>
        ))}
      </group>
      {([-0.8, 0, 0.8] as number[]).map((x, i) => (
        <mesh key={i} position={[x, 0.2, 1.4]} castShadow>
          <cylinderGeometry args={[0.1, 0.1, 0.3, 8]} />
          <meshStandardMaterial color={C.metalShiny} roughness={0.2} metalness={0.9} />
        </mesh>
      ))}
    </group>
  );
}

function PowerMachines() {
  return (
    <group>
      <mesh position={[-0.8, 1.0, 0]} castShadow>
        <boxGeometry args={[1.0, 1.8, 0.8]} />
        <meshStandardMaterial color={C.metal} roughness={0.4} metalness={0.7} />
      </mesh>
      <mesh position={[-0.8, 1.4, 0.41]}>
        <boxGeometry args={[0.6, 0.4, 0.02]} />
        <meshStandardMaterial color="#000a14" emissive="#00e5ff" emissiveIntensity={0.55} />
      </mesh>
      <mesh position={[0.8, 0.9, 0]} castShadow>
        <boxGeometry args={[0.9, 1.6, 0.7]} />
        <meshStandardMaterial color="#4a5568" roughness={0.4} metalness={0.6} />
      </mesh>
      {([0, 0.32, 0.64] as number[]).map((y, i) => (
        <mesh key={i} position={[0.8, 0.4 + y, 0.36]}>
          <sphereGeometry args={[0.07, 8, 8]} />
          <meshStandardMaterial color={i === 0 ? "#76ff03" : i === 1 ? "#ff9100" : "#00e5ff"} emissive={i === 0 ? "#76ff03" : i === 1 ? "#ff9100" : "#00e5ff"} emissiveIntensity={0.9} />
        </mesh>
      ))}
      <mesh position={[0, 0.2, 0.85]} castShadow>
        <boxGeometry args={[2.0, 0.14, 0.12]} />
        <meshStandardMaterial color="#111111" roughness={0.9} />
      </mesh>
    </group>
  );
}

function AssemblyMachines() {
  return (
    <group>
      {([[-1.8, 0, -1.2], [1.8, 0, -1.2], [-1.8, 0, 1.2], [1.8, 0, 1.2]] as [number,number,number][]).map(([x,,z], i) => (
        <mesh key={i} position={[x, 1.2, z]} castShadow>
          <boxGeometry args={[0.18, 2.4, 0.18]} />
          <meshStandardMaterial color={C.woodDark} roughness={0.85} />
        </mesh>
      ))}
      <mesh position={[0, 2.3, -1.2]} castShadow><boxGeometry args={[3.8, 0.2, 0.18]} /><meshStandardMaterial color={C.wood} roughness={0.8} /></mesh>
      <mesh position={[0, 2.3,  1.2]} castShadow><boxGeometry args={[3.8, 0.2, 0.18]} /><meshStandardMaterial color={C.wood} roughness={0.8} /></mesh>
      <mesh position={[0, 2.5, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.12, 0.12, 4.0, 12]} />
        <meshStandardMaterial color={C.metalShiny} roughness={0.15} metalness={0.95} />
      </mesh>
      <mesh position={[0, 0.45, 0]} receiveShadow castShadow>
        <boxGeometry args={[3.4, 0.12, 2.2]} />
        <meshStandardMaterial color={C.wood} roughness={0.8} />
      </mesh>
      <mesh position={[0, 3.1, 0]}>
        <sphereGeometry args={[0.2, 12, 12]} />
        <meshStandardMaterial color="#ff1744" emissive="#ff1744" emissiveIntensity={0.7} roughness={0.4} metalness={0.2} />
      </mesh>
    </group>
  );
}

function FlowParticle({ from, to, color, delay = 0 }: { from: [number,number,number]; to: [number,number,number]; color: string; delay?: number }) {
  const meshRef = useRef<THREE.Mesh>(null!);
  useFrame(({ clock }) => {
    const t = ((clock.getElapsedTime() * 0.32 + delay) % 1);
    if (meshRef.current) {
      meshRef.current.position.x = THREE.MathUtils.lerp(from[0], to[0], t);
      meshRef.current.position.y = THREE.MathUtils.lerp(from[1] + 0.4, to[1] + 0.4, t) + Math.sin(t * Math.PI) * 0.6;
      meshRef.current.position.z = THREE.MathUtils.lerp(from[2], to[2], t);
      meshRef.current.visible = t < 0.96;
    }
  });
  return (
    <mesh ref={meshRef} castShadow>
      <boxGeometry args={[0.3, 0.3, 0.3]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.7} roughness={0.3} metalness={0.4} />
    </mesh>
  );
}

export default function Factory3D({
  onPodClick,
  isLightMode = false,
}: {
  onPodClick: (name: string) => void;
  isLightMode?: boolean;
}) {
  return (
    <div style={{ width: "100%", height: "100%", position: "absolute", top: 0, left: 0 }}>
      <Canvas
        camera={{ position: [2, 12, 20], fov: 48 }}
        shadows
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: isLightMode ? 1.0 : 1.1 }}
        style={{ background: isLightMode ? "#e6edf3" : "#0a0c0f", transition: "background 0.3s ease" }}
      >
        {/* Lighting */}
        <ambientLight color={isLightMode ? 0xffffff : 0x1a2030} intensity={isLightMode ? 1.2 : 0.8} />
        <directionalLight color={0xffffff} intensity={isLightMode ? 1.1 : 0.9} position={[6, 10, 6]} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
        <directionalLight color={isLightMode ? 0xa0c4ff : 0x2040ff} intensity={isLightMode ? 0.4 : 0.3} position={[-5, 3, -3]} />
        <directionalLight color={isLightMode ? 0x0077ff : 0x00e5ff} intensity={0.4} position={[0, 6, -8]} />

        {/* Floor */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
          <planeGeometry args={[80, 80]} />
          <meshStandardMaterial color={isLightMode ? "#dbe3eb" : "#0d1017"} roughness={0.95} metalness={0.05} />
        </mesh>

        {/* Grid lines */}
        <Grid
          args={[60, 60]}
          position={[0, 0.002, 0]}
          cellColor={isLightMode ? "#cbd5e1" : "#1e2530"}
          sectionColor={isLightMode ? "#94a3b8" : "#1a2030"}
          fadeDistance={50}
          fadeStrength={1}
        />

        {DEPT_DEFS.map((d) => (
          <DepartmentPod key={d.name} position={d.pos} color={d.color} emissive={d.emissive} name={d.name} onClick={onPodClick} />
        ))}

        {/* Flow particles: feeder depts -> ASSEMBLY */}
        <FlowParticle from={[-7, 0, -5]} to={[0, 0, 0]} color="#00e5ff" delay={0.0} />
        <FlowParticle from={[-7, 0, -5]} to={[0, 0, 0]} color="#00e5ff" delay={0.55} />
        <FlowParticle from={[ 7, 0, -5]} to={[0, 0, 0]} color="#00e5ff" delay={0.2} />
        <FlowParticle from={[ 7, 0, -5]} to={[0, 0, 0]} color="#00e5ff" delay={0.75} />
        <FlowParticle from={[-7, 0,  5]} to={[0, 0, 0]} color="#ff9100" delay={0.85} />
        <FlowParticle from={[ 7, 0,  5]} to={[0, 0, 0]} color="#00e5ff" delay={0.35} />

        <OrbitControls
          makeDefault
          minPolarAngle={0.1}
          maxPolarAngle={Math.PI / 2 - 0.05}
          minDistance={6}
          maxDistance={40}
        />
      </Canvas>
    </div>
  );
}
